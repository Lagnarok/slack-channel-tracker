#!/usr/bin/env python2.7

import os
from flask import Flask, request
from slackclient import SlackClient

SLACK_TOKEN     = os.environ["SLACK_TOKEN"]
CLIENT_ID       = os.environ["CLIENT_ID"]
CLIENT_SECRET   = os.environ["CLIENT_SECRET"]
OAUTH_SCOPE     = os.environ["OAUTH_SCOPE"]

app = Flask(__name__)

@app.route("/begin_auth", methods=["GET"])
def pre_install():
    return '''
        <a href="https://slack.com/oauth/authorize?scope={0}&client_id={1}">
            Add to Slack
        </a>
    '''.format(OAUTH_SCOPE, CLIENT_ID)

@app.route("/finish_auth", methods=["GET", "POST"])
def post_install():
    auth_code = request.args['code']
    sc = SlackClient("")
    auth_response = sc.api_call(
        "oauth.access",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=auth_code
    )

