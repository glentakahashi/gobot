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
import trueskill
import math

players = {}

env = trueskill.TrueSkill()
cdf = trueskill.choose_backend(None)[0]

def win_probability(a, b):
    deltaMu = sum([x.mu for x in a]) - sum([x.mu for x in b])
    sumSigma = sum([x.sigma ** 2 for x in a]) + sum([x.sigma ** 2 for x in b])
    playerCount = len(a) + len(b)
    denominator = math.sqrt(playerCount * (env.beta * env.beta) + sumSigma)
    return cdf(deltaMu / denominator)

count = 0
correct = 0

with open('hltv_matches.csv', 'rb') as csvfile:
    hltvReader = unicodecsv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    next(hltvReader)
    for row in hltvReader:
        team1 = {}
        team2 = {}
        minGames = 99999
        for player in row[7:12]:
            if player in players:
                team1[player] = players[player]['r']
            else:
                tsplayer = env.create_rating()
                players[player] = {'r': tsplayer, 'games': 1}
                team1[player] = tsplayer
            if players[player]['games'] < minGames:
                minGames = players[player]['games']
        for player in row[12:17]:
            if player in players:
                team2[player] = players[player]['r']
            else:
                tsplayer = env.create_rating()
                players[player] = {'r': tsplayer, 'games': 1}
                team2[player] = tsplayer
            if players[player]['games'] < minGames:
                minGames = players[player]['games']
        winner = 1 if int(row[5]) > int(row[6]) else 2
        predicted_winner = win_probability([players[x]['r'] for x in team1], [players[x]['r'] for x in team2])
        if minGames < 46 and (predicted_winner > .7 or predicted_winner < .3):
            if predicted_winner > .5 and winner == 1 or predicted_winner <= .5 and winner == 2:
                correct += 1
            count += 1
        new_groups = env.rate([team1, team2], ranks=([0,1] if winner == 1 else [1,0]))
        for team in new_groups:
            for player in team:
                players[player]['r'] = team[player]
                players[player]['games'] += 1

print correct, count
print float(correct) / count
