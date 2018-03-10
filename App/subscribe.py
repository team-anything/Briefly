'''
here goes subcriptions from firebase
'''

import re,math,sys,random
import newspaper
import pickle
import pyrebase
from goose3 import Goose
from collections import Counter
import os, datetime
import pandas as pd

max_articles = 5
max_article_addition = 15
ideal = 20.0
n_bullets = 4
stopwords = set()

#firebase initialization
config={
        "apiKey": "AIzaSyCPWujYQAgvfUPh1zqX7jqV51JX0Dj0dnU",
        "authDomain": "briefly-c7ef1.firebaseapp.com",
        "databaseURL": "https://briefly-c7ef1.firebaseio.com",
        "storageBucket": "briefly-c7ef1.appspot.com"
}

email="chiragshetty98@gmail.com"
password="casiitb2016"

firebase = pyrebase.initialize_app(config)
auth=firebase.auth()
user=auth.sign_in_with_email_and_password(email,password)

def refresh(user):
    user=auth.refresh(user['refreshToken'])

db=firebase.database()



def subChannel(sender_id,value):
    try:
        data={'sub':[value]}
        users=db.child("users").order_by_key().equal_to(sender_id).get(user['idToken'])
        # if value in users.val()[sender_id]['sub']:
        #    return
        if(len(users.each())):#check if entry exists
            lis=users.val()[sender_id]['sub']
            lis.append(value)
            data['sub']=lis
            db.child("users").child(sender_id).update(data,user['idToken'])
        else:
            db.child("users").child(sender_id).set(data,user['idToken'])
    except:
        refresh(user)
        subChannel(sender_id,value)

def unsubChannel(sender_id,value):
    try:
        data={}
        users=db.child("users").order_by_key().equal_to(sender_id).get(user['idToken'])
        if(len(users.each())): #check if entry exists
       	    lis=users.val()[sender_id]['sub']
            if value in lis:
                lis.remove(value)
                data['sub']=lis
                db.child("users").child(sender_id).update(data,user['idToken'])
    except:
        refresh(user)
        unsubChannel(sender_id,value)

def addUser(sender_id,value):
    try:
        data = {sender_id:value}
        db.child("id").child(value).set(sender_id,user['idToken'])
    except:
        refresh(user)
        addUser(sender_id,value)

def addSource(url):
    lis=db.child('Ulist').get(user['idToken']).val()
    print(lis)
    lis.append(url)
    db.child('Ulist').set(lis,user['idToken'])

# source , last_updated . hourly limit ( day leaks inactive)
def subscribe_model(source):
    file_name = "sources.csv"
    sources = pd.read_csv(file_name)
    names = list(sources["name"])
    links = list(sources["link"])
    if source not in names:
        return None

    try:
        articles_per_source = db.child("sources").get(user['idToken']).val()
        Uarticle = db.child("article").get(user['idToken']).val()
    except:
        refresh(user)
        subscribe_model(source)

    if source not in articles_per_source.keys():
        if source in names:
            source_url = links[names.index(source)]
            addSource(source_url)
            try:
                articles_per_source = db.child("sources").get(user['idToken']).val()
                Uarticle = db.child("article").get(user['idToken']).val()
            except:
                refresh(user)
                subscribe_model(source)

    n_articles = len(articles_per_source)

    hashes = articles_per_source[source][-min(n_articles,5):]

    results = []
    for hash in hashes:
        if hash in Uarticle.keys():
            results.append(Uarticle[hash])
    return results
    #return articles_per_source[source][-1*min(n_articles-1,5):]

if __name__ == "__main__":
    print(subscribe_model(input()))
