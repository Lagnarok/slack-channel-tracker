#!/usr/bin/env python3

import os
import json
from slackclient import SlackClient

"""
Initializes past state file.
"""

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


out_file = open("past_state.txt", "w")

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

out_file.write(json.dumps(current_channels))
out_file.close()
