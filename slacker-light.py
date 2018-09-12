#!/usr/bin/env python3

import os
import json
import datetime
from slackclient import SlackClient

TRACKED_CHANNEL_PROPERTIES = [
    "name",
    "is_archived",
    "topic",
    "purpose",
    "previous_names",
]

def slack_api_call(next_cursor=False):
    # Connect to the Slack API and load current data
    slack_token = os.environ["SLACK_TOKEN"]
    sc = SlackClient(slack_token)
    if not next_cursor:
        current_state = sc.api_call(
            "channels.list",
            exclude_members=1,
            limit=200
        )
    else:
        current_state = sc.api_call(
            "channels.list",
            exclude_members=1,
            limit=200,
            cursor=next_cursor
        )
    if not current_state["ok"]:
        print("Slack API error encountered: {}".format(current_state["error"]))
        raise SystemExit

    next_cursor = current_state["response_metadata"]["next_cursor"]

    return current_state, next_cursor


def map_to_dict(channel_list):
    """Slack API returns a list of dictionaries. Convert to a dictionary of 
    dictionaries with channel ID as the key.

    Parameters
    ----------
    channel_list : list

    Returns
    -------
    dict
    """
    return {channel["id"]:channel for channel in channel_list}


def compare_dicts(d1, d2):
    """Compare two dictionaries for new items, deleted items, and altered items.
    d1 is past state, d2 is current/future state; this assumption matters for
    subtraction.

    Parameters
    ----------
    d1, d2 : dict

    Returns
    -------
    added : list
        List of keys present in d2 that are not present in d1.
    removed : list
        List of keys present in d1 that are not present in d2.
    modified : dict
        Dictionary of tuples with channel ID as key and tuple as (d1, d2).
        Members are those channels which changed some value between d1 and d2.
    """
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect = d1_keys.intersection(d2_keys)
    added = d2_keys - d1_keys
    removed = d1_keys - d2_keys
    modified = {k : (d1[k], d2[k]) for k in intersect if d1[k] != d2[k]}
    return added, removed, modified


def change_logger(current_channels, past_channels, added, removed, modified, change_log):
    # Any new channels?
    if len(added):
        for channel_id in added:
            change_log.write("Added: {}\n".format(current_channels[channel_id]["name"]))
    else:
        change_log.write("Nothing added.\n")

    # Any deleted channels?
    if len(removed):
        for channel_id in removed:
            change_log.write("Removed: {}\n".format(past_channels[channel_id]["name"]))
    else:
        change_log.write("Nothing removed.\n")

    # Any properties of channels changed?
    if len(modified):
        change_log.write("\nModified Channels listed below. Only changes to {} will be listed.\n".format(
           ", ".join(TRACKED_CHANNEL_PROPERTIES)
        ))
        for channel_id,channel_comparison in modified.items():
            version1 = channel_comparison[0]
            version2 = channel_comparison[1]
            for k,v in version1.items():
                if k in TRACKED_CHANNEL_PROPERTIES and v != version2[k]:
                    change_log.write("Modified {} in {}\n".format(k,version1["name"]))
                    if isinstance(v, dict):
                        try:
                            change_log.write("{}\n->\n{}\n".format(v["value"], version2[k]["value"]))
                        except:
                            change_log.write("{}\n->\n{}\n".format(
                                json.dumps(v, indent=4),
                                json.dumps(version2[k], indent=4)
                            ))
                    else:
                        change_log.write("{} -> {}\n\n".format(v,version2[k]))
    else:
        change_log.write("Nothing modified.\n")


def main():
    # Load the data from the previous run
    try:
        past_state_file = open("past_state.txt", 'r')
    except IOError:
        print("Failed to open past_state.txt for reading")
        raise
    else:
        past_state_str = past_state_file.read()
        past_state_file.close()
        past_state = json.loads(past_state_str)
    
    # Current time in UTC, in ISO format, without sub-second precision
    timestamp = datetime.datetime.utcnow().isoformat().split('.')[0]
    try:
        change_log = open("change_log_{}.txt".format(timestamp), 'w')
    except IOError:
        print("Failed to create/open change_log_{}.txt".format(timestamp))
        raise

    # This won't change for the duration of a run
    past_channels = map_to_dict(past_state["channels"])

    # First API call; no known cursor to next page
    current_state, next_cursor = slack_api_call()
    current_channels = {}
    
    # If there aren't pages, just run once.
    if not next_cursor:
        current_channels = map_to_dict(current_state["channels"])

    # If there are pages, spool them into current_channels until they run out.
    while next_cursor:
        print(next_cursor)
        current_channels.update(map_to_dict(current_state["channels"]))
        current_state, next_cursor = slack_api_call(next_cursor)
    
    added, removed, modified = compare_dicts(past_channels, current_channels)
    change_logger(current_channels, past_channels, added, removed, modified, change_log)

        
    change_log.close()

if __name__ == "__main__":
    main()

#past_state_file = open("past_state.txt", 'w')
#past_state_file.write(json.dumps(response))
#past_state_file.close()

