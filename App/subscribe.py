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

def summary(url):
    g = Goose()
    article = g.extract(url)
    title = article.title
    publish_date = "None"
    headlines = []
    if title == None :
        title = url
    try:
        image = article.top_image.src
    except Exception:
        if len(article.images)>0:
            image = article.images[0]
        else:
            image = "http://www.sahalnews.com/wp-content/uploads/2014/12/news-update-.jpg"
    for bullets in summarize(url,title,article.cleaned_text,n_bullets):
        headlines.append(bullets)
    if len(headlines)==0:
        headlines = [url,url]
    return (title,publish_date,image,headlines)


def load_stopwords(language):
    """
    Loads language-specific stopwords for keyword selection
    """
    global stopwords

    # stopwords for nlp in English are not the regular stopwords
    # to pass the tests
    # can be changed with the tests
    if language == 'en':
        stopwordsFile =".stopwords/stopwords-nlp-en.txt"
    else:
        stopwordsFile = path.join(settings.STOPWORDS_DIR,\
                                  'stopwords-{}.txt'.format(language))
    with open(stopwordsFile, 'r', encoding='utf-8') as f:
        stopwords.update(set([w.strip() for w in f.readlines()]))


def summarize(url='', title='', text='', max_sents=5):
    if not text or not title or max_sents <= 0:
        return []

    summaries = []
    sentences = split_sentences(text)
    keys = keywords(text)
    titleWords = split_words(title)

    # Score sentences, and use the top 5 or max_sents sentences
    ranks = score(sentences, titleWords, keys).most_common(max_sents)
    for rank in ranks:
        summaries.append(rank[0])
    summaries.sort(key=lambda summary: summary[0])
    return [summary[1] for summary in summaries]


def score(sentences, titleWords, keywords):
    """Score sentences based on different features
    """
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = split_words(s)
        titleFeature = title_score(titleWords, sentence)
        sentenceLength = length_score(len(sentence))
        sentencePosition = sentence_position(i + 1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0
        # Weighted average of scores from four categories
        totalScore = (titleFeature*1.5 + frequency*2.0 +
                      sentenceLength*1.0 + sentencePosition*1.0)/4.0
        ranks[(i, s)] = totalScore
    return ranks

def sbs(words, keywords):
    score = 0.0
    if (len(words) == 0):
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score) / 10.0

def dbs(words, keywords):
    if (len(words) == 0):
        return 0
    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1] * second[1]) / (dif ** 2)
    # Number of intersections
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return (1 / (k * (k + 1.0)) * summ)

def split_words(text):
    """Split a string into array of words
    """
    try:
        text = re.sub(r'[^\w ]', '', text)  # strip special chars
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        return None

def keywords(text):
    """Get the top 10 keywords and their frequency scores ignores blacklisted
    words in stopwords, counts the number of occurrences of each word, and
    sorts them in reverse natural order (so descending) by number of
    occurrences.
    """
    NUM_KEYWORDS = 10
    text = split_words(text)
    # of words before removing blacklist words
    if text:
        num_words = len(text)
        text = [x for x in text if x not in stopwords]
        freq = {}
        for word in text:
            if word in freq:
                freq[word] += 1
            else:
                freq[word] = 1

        min_size = min(NUM_KEYWORDS, len(freq))
        keywords = sorted(freq.items(),
                          key=lambda x: (x[1], x[0]),
                          reverse=True)
        keywords = keywords[:min_size]
        keywords = dict((x, y) for x, y in keywords)

        for k in keywords:
            articleScore = keywords[k] * 1.0 / max(num_words, 1)
            keywords[k] = articleScore * 1.5 + 1
        return dict(keywords)
    else:
        return dict()

def split_sentences(text):
    """Split a large string into sentences
    """
    import nltk.data
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    sentences = tokenizer.tokenize(text)
    sentences = [x.replace('\n', '') for x in sentences if len(x) > 10]
    return sentences

def length_score(sentence_len):
    return 1 - math.fabs(ideal - sentence_len) / ideal

def title_score(title, sentence):
    if title:
        title = [x for x in title if x not in stopwords]
        count = 0.0
        for word in sentence:
            if (word not in stopwords and word in title):
                count += 1.0
        return count / max(len(title), 1)
    else:
        return 0

def sentence_position(i, size):
    """Different sentence positions indicate different
    probability of being an important sentence.
    """
    normalized = i * 1.0 / size
    if (normalized > 1.0):
        return 0
    elif (normalized > 0.9):
        return 0.15
    elif (normalized > 0.8):
        return 0.04
    elif (normalized > 0.7):
        return 0.04
    elif (normalized > 0.6):
        return 0.06
    elif (normalized > 0.5):
        return 0.04
    elif (normalized > 0.4):
        return 0.05
    elif (normalized > 0.3):
        return 0.08
    elif (normalized > 0.2):
        return 0.14
    elif (normalized > 0.1):
        return 0.23
    elif (normalized > 0):
        return 0.17
    else:
        return 0

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

    n_articles = len(articles_per_source[source])

    hashes = articles_per_source[source][-min(n_articles,5):]
    results = []
    for hash in hashes:
        if hash in Uarticle.keys():
            results.append(Uarticle[hash])
    return results
    #return articles_per_source[source][-1*min(n_articles-1,5):]

if __name__ == "__main__":
    print(subscribe_model(input()))
