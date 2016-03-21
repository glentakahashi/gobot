#!/usr/local/bin/python

import random
import datetime
import unicodecsv
import csv
import time
import urllib2
import numpy as np
import urllib2
from bs4 import BeautifulSoup
import re
import csv
import os
from time import gmtime, strftime
import datetime
import unicodecsv
from scipy.sparse import coo_matrix, hstack, vstack
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer

training_data = [[],[],[]]
training_data2 = [[],[],[]]
actual_data = [[],[],[]]

training_data_indices = []
training_data_indices2 = []
texts = []

def toepoch(d):
    return int(time.mktime(datetime.datetime.strptime(d, '%d/%m %y').timetuple()))

with open('hltv_org_matches_2014.csv', 'rb') as csvfile:
    hltvReader = unicodecsv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    next(hltvReader)
    i = 0
    for row in hltvReader:
        asText = ' '.join(['team1a' + row['teamid1'], 'team2a' + row['teamid2'], row['map']])
        asText2 = ' '.join(['team2a' + row['teamid1'], 'team1a' + row['teamid2'], row['map']])
        intdate = toepoch(row['date'])
        winner = 1 if int(row['score1']) > int(row['score2']) else 2
        winner2 = 3 - winner
        if random.random() < .95:
            training_data_indices.append(i)
            training_data[0].append(intdate)
            training_data[0].append(intdate)
            #training_data[1].append(asText)
            training_data[2].append(winner)
            training_data[2].append(winner2)
        if i < 11000:
            training_data_indices2.append(i)
            training_data2[0].append(intdate)
            training_data2[0].append(intdate)
            #training_data[1].append(asText)
            training_data2[2].append(winner)
            training_data2[2].append(winner2)
        texts.append(asText)
        texts.append(asText2)
        actual_data[0].append(intdate)
        actual_data[0].append(intdate)
        #actual_data[1].append(asText)
        actual_data[2].append(winner)
        actual_data[2].append(winner2)
        i += 2

vectorizer = CountVectorizer()
features = vectorizer.fit_transform(texts)
actual_data[1] = hstack(([[x] for x in actual_data[0]],features), 'csr')

j = 0
for i in training_data_indices:
    training_data[1].append(hstack([training_data[0][j],features[i]]))
    training_data[1].append(hstack([training_data[0][j],features[i+1]]))
    j += 1
j = 0
for i in training_data_indices2:
    training_data2[1].append(hstack([training_data2[0][j],features[i]]))
    training_data2[1].append(hstack([training_data2[0][j],features[i+1]]))
    j += 1

#training_data_condensed = [csr_matrix(x) + y for x in training_data[0] for y in training_data[1]]
#training_data_actual = [training_data_condensed, training_data[2]]

#actual_data_condensed = [[x] + y for x in actual_data[0] for y in actual_data[1]]
#actual_data_actual = [actual_data_condensed, actual_data[2]]

#print training_data[1][0], training_data[2][0]
#print '===='
#print actual_data[1][0], actual_data[2][0]

#print len(training_data)
#print len(actual_data)

for qq in range(10,50,5):
    tests = 0
    correct = 0
    correct2 = 0
    same = 0

    clf = RandomForestClassifier(n_estimators=qq)
    clf.fit(vstack(training_data[1]),training_data[2])
    clf2 = RandomForestClassifier(n_estimators=qq)
    clf2.fit(vstack(training_data2[1]),training_data2[2])
    #clf2 = svm.SVC(probability=True)
    #clf2.fit(vstack(training_data[1]),training_data[2])

    for i in range(0,len(actual_data[0])):
        if i not in training_data_indices and i not in training_data_indices2 and i-1 not in training_data_indices and i-1 not in training_data_indices2:
            tests += 1
            res = clf.predict(actual_data[1][i])
            res2 = clf2.predict(actual_data[1][i])
            if res == res2:
                same += 1
            if res == actual_data[2][i]:
                #print "success!"
                correct += 1
            if res2 == actual_data[2][i]:
                #print "success!"
                correct2 += 1
            # else:
                # print "failure :("

    print tests, correct
    print float(correct) / tests
    print float(correct2) / tests
    print float(same) / tests

def getPlayersForTeam(matchId, team):
    hltvUrl = 'http://www.hltv.org/?pageid=188&statsfilter=0&matchid=' + matchId
    hltvReq = urllib2.Request(hltvUrl, headers={
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'Cookie': '__cfduid=d1058c763c84c3a07a9e877717746c8c01448777981; cookieconsent_dismissed=yes',
        })
    hltvCon = urllib2.urlopen(hltvReq)
    hltvHTML = hltvCon.read()
    hltvSoup = BeautifulSoup(hltvHTML, 'html.parser')

    players = hltvSoup.select('div.covMainBoxContent > div > div > div')
    teamplayers = []
    for player in players:
        ids = [re.search('(teamid|playerid)=?(\d*)', link.get('href')).group(2) for link in player.select("div > a")]
        if len(ids) != 2:
            continue
        playerId = ids[0]
        teamId = ids[1]
        if teamId == team:
            teamplayers.append(playerId)
    if len(teamplayers) != 5:
        print "%s had %s players for some reason" % (matchId, len(teamplayers))

    while len(teamplayers) < 5:
        teamplayers += ['0']

    return teamplayers

def predictGame(clf, vectorizer, date, team1, team2,m):
    asText = ' '.join(['team1a' + team1, 'team2a' + team2, m])
    asText2 = ' '.join(['team2a' + team1, 'team1a' + team2, m])
    print asText
    print asText2
    pred1 = clf.predict_proba(hstack([toepoch('%s'%date),vectorizer.transform([asText])]))
    pred2 = clf.predict_proba(hstack([toepoch('%s'%date),vectorizer.transform([asText2])]))
    return (pred1 + pred2) / 2

while True:
    date = raw_input('date: ')
    team1 = raw_input('team1: ')
    team2 = raw_input('team2: ')
    m = raw_input('map: ')
    print predictGame(clf,vectorizer,date,team1,team2,m)
    print predictGame(clf2,vectorizer,date,team1,team2,m)
