# -*- coding: utf-8 -*-
import re,math,sys,random
import newspaper
import pickle
import pyrebase
from collections import Counter
import os, datetime
import pandas as pd
import string

max_articles = 5
max_article_addition = 15
ideal = 20.0
n_bullets = 4
stopwords = set()

INDIAN_LANGUAGES = ['hi','guj','ma']

def summary(text,title,lang):
    summar = []
    if lang not in INDIAN_LANGUAGES:
        print("Booyeah")
        return title

    if title == None :
        title = "testing"
    load_stopwords()
    for bullets in summarize(text=text,title=title,lang=lang):
        summar.append(bullets)
    if len(summar)==0:
        summar = title
    return summar

def load_stopwords():
    global stopwords
    lines = open("./stopwords-hi.txt","r")
    stopwords = [word[:-1] for word in lines.readlines()]


def summarize(title="",text="",lang="",max_sents = 3):
    if not text or not title or max_sents <= 0:
        return []

    summaries = []
    sentences = indian_sent(text)
    keys = keywords(text)
    titleWords = indian_word(title)
    # Score sentences, and use the top 5 or max_sents sentences
    ranks = score(sentences, titleWords, keys).most_common(max_sents)
    for rank in ranks:
        summaries.append(rank[0])
    summaries.sort(key=lambda summary: summary[0])
    return [summary[1] for summary in summaries]


def score(sentences, titleWords, keywords):
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = indian_word(s)
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

def keywords(text):
    NUM_KEYWORDS = 10
    text = indian_word(text)
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

indian_punctuation_pattern = re.compile('(['+string.punctuation+'\u0964\u0965'+'])')


def indian_word(untokenized_string: str):
    modified_punctuations = string.punctuation.replace("|","") # The replace , deletes the ' | ' from the punctuation string provided by the library
    indian_punctuation_pattern = re.compile('(['+modified_punctuations+'\u0964\u0965'+']|\|+)')
    tok_str = indian_punctuation_pattern.sub(r' \1 ',untokenized_string.replace('\t',' '))
    return re.sub(r'[ ]+',u' ',tok_str).strip(' ').split(' ')

def indian_sent(untokenized_string:str):
    tok_str = indian_punctuation_pattern.sub(r' \1 ',untokenized_string.replace('\t',' '))
    x = re.sub(r'[ ]+',u' ',tok_str).strip('|').split(".")
    return x


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
