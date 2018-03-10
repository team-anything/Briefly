import re,math,sys
import newspaper
import pickle
import pyrebase
from collections import Counter
import os, datetime
import random
import hashlib
import time
import pandas as pd
from langdetect import detect       # indian language plug. works for hindi  . TODO : rest of indian languages
import indian_scraper_plug
max_article_addition = 15
ideal = 20.0
n_bullets = 4
stopwords = set()


INDIAN_LANGUAGES = ['hi','guj','ma']

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


def addSource(url):
    lis=db.child('Ulist').get(user['idToken']).val()
    print(lis)
    if url not in lis:
        lis.append(url)
    db.child('Ulist').set(lis,user['idToken'])

def cleanSource():
   lis=db.child('Ulist').get(user['idToken']).val()
   clist=[]
   for i in lis:
       if i!=None:
           clist.append(i)
   print(clist)
   db.child('Ulist').set(clist,user['idToken'])

# source , last_updated . hourly limit ( day leaks inactive)
def subscribe_model(url,Mf=True):
    #load_stopwords('en')
    try:
        articles_per_source = db.child("sources").get(user['idToken']).val()
        Uarticle = db.child("article").get(user['idToken']).val()
    except:
        refresh(user)
        subscribe_model(url)
    print(len(Uarticle))
    file_name = "sources.csv"
    sources = pd.read_csv(file_name)
    names = list(sources["name"])
    #print(names)
    links = list(sources["link"])
    #print(links)

    if url not in links:
        print("not in sources.csv")
        return None

    source = names[links.index(url)]
    print(source)

    if source in articles_per_source.keys():
        ls = articles_per_source[source]
    else:
        ls=[]
        # check this out 
    links = newspaper.build(url,memoize_articles=Mf)  #turn this True while in serev
    print(len(links.articles))
    #print(links.articles)
    for article in links.articles[:min(15,len(links.articles))]:
        a=hashlib.sha224(article.url.encode('utf-8')).hexdigest()
        article.download()
        article.parse()
        title = article.title
        date = ""
        try:
            image=article.top_image
        except:
            image = "http://www.sahalnews.com/wp-content/uploads/2014/12/news-update-.jpg"
        article.nlp()

        # detect here
        iso_lang = detect(title)
        
        if iso_lang in INDIAN_LANGUAGES:
            summary = indian_scraper_plug.summary(article.text,article.title,iso_lang)
        else:
            summary = article.summary
        ls.append(a)
        Uarticle[a]=[article.url,title,date,image,summary]
    articles_per_source[source]=ls
    print('khatam')
    articles_per_source[source]=ls
    '''
    print(len(Uarticle))
    print(Uarticle)
    print("==========================")
    print(ls)
    '''
    try:
        db.child("sources").set(articles_per_source,user['idToken'])
        db.child("article").set(Uarticle,user['idToken'])
    except:
        refresh(user)
        db.child("sources").set(articles_per_source,user['idToken'])
        db.child("article").set(Uarticle,user['idToken'])

def scrape(n=0):
    lis=db.child('Ulist').get(user['idToken']).val()
    if(lis[n]):
        subscribe_model(lis[n])
    print('sleeping....')
    time.sleep(5)
    if(n+1==len(lis)):
        return
    scrape((n+1)%len(lis))

if __name__ == "__main__":
    scrape(0)
