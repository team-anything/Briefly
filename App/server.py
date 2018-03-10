# coding: utf-8

dummy = "***"*100

'''
has globals : primary_key
'''

import os,random
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from flask import Flask, request, send_from_directory, render_template

import pickle
import messenger
import subscribe
from config import CONFIG
import newspaper
from newspaper import Config
from fbpage import page
from fbmq import Attachment,Template,QuickReply
import pandas as pd
import apiai
import json
app = Flask(__name__)


@app.route('/webhook', methods=['GET'])
def validate():
    if request.args.get('hub.mode', '') == 'subscribe' and \
                    request.args.get('hub.verify_token', '') == CONFIG['VERIFY_TOKEN']:

        print("Validating webhook")

        return request.args.get('hub.challenge', '')
    else:
        return 'Failed validation. Make sure the validation tokens match.'

page.show_starting_button("START_PAYLOAD")       # Getting Started

@page.callback(['START_PAYLOAD'])
def start_callback(payload, event):
    sender_id = event.sender_id
    quick_replies = [
            QuickReply(title="Yeah !", payload="PICK_SYNC"),
            QuickReply(title="Nah ", payload="PICK_DSYNC")
            ]
    page.send(sender_id, "Would you like to sync this conversation :P ?\n you can subscribe etc. ",quick_replies=quick_replies,metadata="DEVELOPER_DEFINED_METADATA")
    print("Let's start!")

@page.callback(['PICK_SYNC', 'PICK_DSYNC'])
def callback_picked_genre(payload, event):
    sender_id = event.sender_id
    if payload == "PICK_SYNC":
        page.send(sender_id,"Please Share your Briefly username \n ( format id: username ) ")      #  TODO
    else:
        page.send(sender_id,"Okay , go ahead . Play Around for some time ")

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    print(payload)
    page.handle_webhook(payload)
    page.show_persistent_menu([Template.ButtonPostBack('SOURCES', 'MENU_PAYLOAD/1'),
                           Template.ButtonPostBack('SUBSCRIBE', 'MENU_PAYLOAD/2')])
    page.handle_webhook(payload,message = message_handler)

    return "ok"

@page.handle_message
def message_handler(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    message = event.message_text
    user_profile = page.get_user_profile(sender_id)
    user_name = user_profile["first_name"]

    # try Menu
    buttons = [
        Template.ButtonWeb("Open Web URL", "https://www.codeforces.com"),
        Template.ButtonPostBack("Subscribe", "www.nytimes.com"),
        Template.ButtonPhoneNumber("Call Phone Number", "+91")
    ]

    page.typing_on(sender_id)
    page.typing_off(sender_id)
    if message == "Get Menu":
        page.send(sender_id, Template.Buttons("Here you go , %s .." %(user_name) , buttons))
    else:
        page.send(sender_id,"Didn't get you")
# test_persistant menu 
@page.callback(['MENU_PAYLOAD/(.+)'])
def click_persistent_menu(payload, event):
    click_menu = payload.split('/')[1]
    page.send(event.sender_id,"you clicked %s menu" % (click_menu))

@app.route('/authorize', methods=['GET'])
def authorize():
    account_linking_token = request.args.get('account_linking_token', '')
    redirect_uri = request.args.get('redirect_uri', '')

    auth_code = '1234567890'

    redirect_uri_success = redirect_uri + "&authorization_code=" + auth_code

    return render_template('authorize.html', data={
        'account_linking_token': account_linking_token,
        'redirect_uri': redirect_uri,
        'redirect_uri_success': redirect_uri_success
    })



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True,debug=True,use_reloader=False)
