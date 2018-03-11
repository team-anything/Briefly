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


max_sentences = 3
max_local_summaries = 20
SUMMARIES = dict()
previous = "nytimes"

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
    page.send(sender_id, "Would you like to sync this conversation ?\n you can subscribe etc. ",quick_replies=quick_replies,metadata="DEVELOPER_DEFINED_METADATA")
    print("Let's start!")

@page.callback(['PICK_SYNC', 'PICK_DSYNC'])
def callback_picked_genre(payload, event):
    sender_id = event.sender_id
    if payload == "PICK_SYNC":
        page.send(sender_id,"Please Share your *Briefly* username \n ( format id: username ) ")      # TODO
    else:
        page.send(sender_id,"Go ahead ;) Play Around for some time ")

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    print(payload)
    page.show_persistent_menu([Template.ButtonPostBack('SUB_LIST1', 'MENU_PAYLOAD/1'),
                           Template.ButtonPostBack('SUB_LIST2', 'MENU_PAYLOAD/2')])
    page.handle_webhook(payload,message = message_handler)

    return "ok"

@page.handle_message
def message_handler(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    message = event.message_text

    # try Menu
    buttons = [
        Template.ButtonWeb("Open Web URL", "https://www.codeforces.com"),
        Template.ButtonPostBack("Subscribe", "www.nytimes.com"),
        Template.ButtonPhoneNumber("Call Phone Number", "+91")
    ]

    user_profile = page.get_user_profile(sender_id)

    page.typing_on(sender_id)
    page.typing_off(sender_id)

    #print(user_profile)
    if bot(message,sender_id):
        print("Bot results")
    else:
        page.send(sender_id,"Didn't get you ")


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

# only issue , sends blobs
##@app.before_first_request
def bot(text_message,sender_id):

    Access_token = "8f88a5431e7d4bc1b07470b6e3eeee7d"
    client = apiai.ApiAI(Access_token)
    req = client.text_request()
    req.lang = "de"
    req.session_id = "<SESSION ID, UNIQUE FOR EACH USER>"
    req.query = text_message
    response = json.loads(req.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']

    if responseStatus==200 :
        text = response['result']['fulfillment']['speech']
    else:
        text="No Match Found"

    if len(response['result']['contexts']):
        context = response['result']['contexts'][0]['parameters'] #extract parameters
        Query = context['type'] #get the type of query
        shorten_name = context['News'] #get the value of news
        print(context)
        if Query == "subscribe" :
            text = "added "+shorten_name+" to your feed"
            page.send(sender_id,text)
            #print(type(sender_id))
            #print(shorten_name)
            subscribe.subChannel(str(sender_id),shorten_name)
        elif Query == "unsubscribe":
            text = "removing "+shorten_name+" from your feed"
            page.send(sender_id,text)
            subscribe.unsubChannel(str(sender_id),shorten_name)
        elif Query == "summary":
            text="generating your summary"
            page.send(sender_id,text)
            url = text_message.split()[-1]
            if 'http' not in url:
                url='https://'+url
            title,publish_date,image,headline = subscribe.summary(url)
            sumar = ""
            for h in headline:
                sumar += h
            text = title+" \n "+sumar
            page.send(sender_id,text)
        elif Query == "id":
            user_name = text_message.split()[-1]
            subscribe.addUser(sender_id,user_name)
            text = "You've been synced "
            page.send(sender_id,text)
            print("User Added")
        else:
            print("here")
            text="loading the latest news from "+shorten_name
            page.send(sender_id,text)
            # page.send(sender_id,"Entity : %s \nValue : %s \nConfidence : %s "%(entin[0],result[entin[0]][0]['value'],result[entin[0]][0]['confidence']*100))
            visit = 1
            results = generate_summaries(shorten_name,max_sentences,visit)
            if results == False:
                return False
            # gen articles send 1st
            page.send(sender_id,Template.Generic(results))
            previous = shorten_name
            load_more = [
                        QuickReply(title="Load More", payload="LOAD_MORE"+str(visit))
                        ]
            page.send(sender_id,"Do you want to load more ?",quick_replies=load_more,metadata="DEVELOPER_DEFINED_METADATA")

            # page.send(sender_id, Template.Buttons(results[1][:200],results[2]))
        return True
    else:
        page.send(sender_id,text)
        return True
        '''
        ListView Template
        page.send(sender_id,Template.List(elements = results,top_element_style='large',
            buttons=[
                { "title": "View Less", "type": "postback", "payload": "payload"}]))
        '''

@page.callback(['LOAD_MORE(.+)'])
def callback_picked_genre(payload, event):
    sender_id = event.sender_id
    print("picked load more")
    text="loading the latest news from "+ previous
    page.send(sender_id,text)
    visit = int(payload[9:])+1
    results = generate_summaries(previous,max_sentences,visit)
    if results == False:
        return False
    # gen articles send 1st
    page.send(sender_id,Template.Generic(results))
    

def generate_summaries(name,sentences,visit):
    # NOTE : we don't need to store summary , instead storing the links would be enough .

    articles = subscribe.subscribe_model(name,visit)      # link , headline , date==None , image_url , sentences(list)
    if articles == None :
        return False
    results = []
    '''
    Set a "View More Articles" Option Over here instead of max_articles
    '''
    for article in articles:
        # breakpoint tests
        '''
        Issue : Default use of Generic Template <subtitle section> 60chars, <title section> 60 chars ,List view( No - Image ) 640 chars

        '''
        article_url = article[0]
        headline = article[1]
        publish_date = article[2]
        top_image_url  = article[3]
        summary_list = []
        concate_news = headline
        if len(article)==5:
            concate_news = article[4]

        # recheck TODO
        sum_keys = sorted(SUMMARIES.keys())

        if len(sum_keys) > max_local_summaries :
            del SUMMARIES[sum_keys[0]]

        if not len(sum_keys):
            hash_index = 0
        else:
            hash_index = sum_keys[-1]

        results.append(Template.GenericElement(headline,
                subtitle = name ,
                image_url = top_image_url,
                buttons=[
                        Template.ButtonWeb("Read More", article_url),
                        Template.ButtonPostBack("Summarize", "DEVELOPED_DEFINED_PAYLOAD" + str(hash_index+1)),    #     maybe a SHARE button ?
                            # Template.ButtonPhoneNumber("Call Phone Number", "+16505551234")
                        ])
                )
        SUMMARIES[hash_index+1] = [top_image_url,concate_news]
    print("reached Line:227")
    return results

# Triggered off "PostBack Called"
@page.callback(['DEVELOPED_DEFINED_PAYLOAD(.+)'],types=['POSTBACK'])
def callback_clicked_button(payload,event):
    sender_id = event.sender_id
    news_id = int(payload[25:])      # bug
    print(dummy)
    print(news_id)
    image_url = SUMMARIES[news_id][0]
    summ_ary = SUMMARIES[news_id][1]
    # do something with these text   -> To add Headline
    page.send(sender_id,Attachment.Image(image_url))
    page.send(sender_id,summ_ary)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True,debug=True,use_reloader=False)
