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
from scipy.sparse import coo_matrix, hstack, vstack, csr_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.cross_validation import KFold
import matplotlib.pyplot as plt
import itertools
from sklearn import metrics

def toepoch(d):
    return int(time.mktime(datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S').timetuple()))

dates = []
winners = []
matchups = []

players = {}

with open('hltv_matches.csv', 'rb') as csvfile:
    hltvReader = unicodecsv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    next(hltvReader)
    for row in hltvReader:
        team1 = row[7:12]
        team2 = row[12:17]
        for player in (team1 + team2):
            if player in players:
                players[player] += 1
            else:
                players[player] = 1
        intdate = toepoch(row[0])
        winner = 1 if int(row[5]) > int(row[6]) else -1
        dates.append(intdate)
        matchups.append([team1, team2])
        winners.append(winner)

vectorizer = CountVectorizer()
features = vectorizer.fit_transform(set(itertools.chain(*[x[0] + x[1] for x in matchups])))
for minGames in range(0,500,50):
    print "Minimum number of games: %d" % minGames
    games = ([], [])
    for i in range(len(matchups)):
        c = False
        for player in matchups[i][0] + matchups[i][1]:
            if players[player] < minGames:
                c = True
        if c:
            continue
        date = dates[i]
        team1vec = vectorizer.transform([' '.join(matchups[i][0])])
        team2vec = vectorizer.transform([' '.join(matchups[i][1])])
        winner = winners[i]
        #forwards
        games[0].append(hstack([[date],team1vec - team2vec]))
        games[1].append(winner)
        #reverse
        games[0].append(hstack([[date],team2vec - team1vec]))
        games[1].append(-1 * winner)
    print len(games[0])
    continue

    minAccuracy = 100
    worstNEstimators = 0
    worstLearningRate = 0
    worstMaxDepth = 0
    maxAccuracy = 0
    bestNEstimators = 0
    bestLearningRate = 0
    bestMaxDepth = 0
    for i in range(0,100):
        print "Test #%d" % (i+1)
        n_estimators = random.randint(500,5000)
        learning_rate = random.uniform(.1,1)
        max_depth = random.randint(1,6)
        kf = KFold(len(games[0]), n_folds=5, shuffle=True)
        n = 0
        for train_indices, test_indices in kf:
            n += 1
            print "Fold %d of 5" % n
            trainX = vstack([games[0][i] for i in train_indices])
            trainY = [games[1][i] for i in train_indices]
            clf = GradientBoostingClassifier(n_estimators=1000, learning_rate=1, max_depth=4, random_state=0)
            clf.fit(trainX,trainY)
            guesses = []
            actual = [games[1][i] for i in test_indices]
            correct = 0
            errors = []
            confidences = []
            for i in test_indices:
                prob1, prob2 = clf.predict_proba(games[0][i].toarray())[0]
                confidence = abs(prob1 - .5) * 200
                guesses.append(prob2)
                if prob2 > prob1 and games[1][i] == 1 or prob1 > prob2 and games[1][i] == -1:
                    correct += 1
                    confidences.append(confidence)
                    #print "Correct, confidence = %.2f" % confidence
                else:
                    errors.append(confidence)
                    #print "Incorrect, error    = %.2f" % confidence
            # fpr, tpr, thresholds = metrics.roc_curve(np.array(actual), np.array(guesses), pos_label=1)
            # plt.figure(i)
            # plt.plot(fpr, tpr)
            # plt.show()
            accuracy = float(correct)/len(test_indices)*100
            if accuracy < minAccuracy:
                minAccuracy = accuracy
                worstNEstimators = n_estimators
                worstLearningRate = learning_rate
                worstMaxDepth = max_depth
            if accuracy > maxAccuracy:
                maxAccuracy = accuracy
                bestNEstimators = n_estimators
                bestLearningRate = learning_rate
                bestMaxDepth = max_depth
            print "Average error: %.2f, Average confidence: %.2f" % ((sum(errors) / len(errors)), (sum(confidences) / len(confidences)))
            print "Correct: %.2f%%, Settings: n_estimators = %d, learning_rate = %.2f, max_depth = %d"%(accuracy, n_estimators, learning_rate, max_depth)
    print "Best accuracy: %.2f%%, Settings: n_estimators = %d, learning_rate = %.2f, max_depth = %d"%(maxAccuracy, bestNEstimators, bestLearningRate, bestMaxDepth)
    print "Worst accuracy: %.2f%%, Settings: n_estimators = %d, learning_rate = %.2f, max_depth = %d"%(minAccuracy, worstNEstimators, worstLearningRate, worstMaxDepth)

quit()

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

def predictGame(clf, vectorizer, date, matchId1, matchid2, team1, team2):
    team1players = getPlayersForTeam(matchId1, team1)
    team2players = getPlayersForTeam(matchId2, team2)
    asText = ' '.join(['team1a' + x for x in team1players] + ['team2a' + x for x in team2players])
    asText2 = ' '.join(['team2a' + x for x in team1players] + ['team1a' + x for x in team2players])
    print asText
    print asText2
    pred1 = clf.predict_proba(hstack([toepoch('%s 00:00:00'%date),vectorizer.transform([asText])]).toarray())
    pred2 = clf.predict_proba(hstack([toepoch('%s 00:00:00'%date),vectorizer.transform([asText2])]).toarray())
    return pred1, pred2

while True:
    date = raw_input('date: ')
    matchId1 = raw_input('matchId1: ')
    team1 = raw_input('team1: ')
    matchId2 = raw_input('matchId2: ')
    team2 = raw_input('team2: ')
    print predictGame(clf,vectorizer,date,matchId1,matchId2,team1,team2)
    print predictGame(clf2,vectorizer,date,matchId1,matchId2,team1,team2)
