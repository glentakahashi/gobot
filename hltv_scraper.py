#!/usr/local/bin/python
# scrape HLTV results for CS:GO Matches

# get website content
import urllib2
from bs4 import BeautifulSoup
import re
import csv
import os
from time import gmtime, strftime
import datetime
import unicodecsv

def getMatchInfo(matchId, team1, team2):
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
    team1players = []
    team2players = []
    for player in players:
        ids = [re.search('(teamid|playerid)=?(\d*)', link.get('href')).group(2) for link in player.select("div > a")]
        if len(ids) != 2:
            continue
        playerId = ids[0]
        teamId = ids[1]
        if teamId == team1:
            team1players.append(playerId)
        else:
            team2players.append(playerId)
    if len(team1players + team2players) != 10:
        print "%s had %s players for some reason" % (matchId, len(team1players + team2players))

    while len(team1players) < 5:
        team1players += ['0']
    while len(team2players) < 5:
        team2players += ['0']

    matchPage = hltvSoup.select('div.mainAreaNoHeadline > div.centerNoHeadline > div > div > div.covGroupBoxContent > div > div > div.covSmallHeadline > a')[0]
    if matchPage.get_text() == 'Match page':
        matchPageUrl = matchPage.get('href')
    else:
        matchPageUrl = ''

    return team1players[:5] + team2players[:5], matchPageUrl

# extract match information and format to list
def formatMatch(hltvMatch):
    hltvMatchNames = hltvMatch.get_text(";", strip = True)
    hltvMatchScore = re.findall('\((\d*?)\)', hltvMatchNames)
    hltvMatchIds = [re.search('(teamid|matchid|eventid)=?(\d*)', link.get('href')).group(2) for link in hltvMatch.select("a")]
    hltvMatchDate = datetime.datetime.strptime(hltvMatchNames.split(';')[0], '%d/%m %y')
    hltvMatchSplit = hltvMatchNames.split(';')
    hltvMatchMap = hltvMatchSplit[3]
    team1name = re.match("(.*) \(\d+\)", hltvMatchSplit[1]).group(1)
    team2name = re.match("(.*) \(\d+\)", hltvMatchSplit[2]).group(1)
    if hltvMatchIds[0] in found:
        return None
    matchInfo = getMatchInfo(hltvMatchIds[0],hltvMatchIds[1],hltvMatchIds[2])
    hltvMatchLine = [hltvMatchDate] + hltvMatchIds + hltvMatchScore + matchInfo[0] + [hltvMatchMap, team1name, team2name, matchInfo[1]]
    return hltvMatchLine

# gets all matches from one page
def getMatchesOfPage(hltvUrl):
    hltvReq = urllib2.Request(hltvUrl, headers={
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'Cookie': '__cfduid=d1058c763c84c3a07a9e877717746c8c01448777981; cookieconsent_dismissed=yes',
        })
    hltvCon = urllib2.urlopen(hltvReq)
    hltvHTML = hltvCon.read()
    hltvSoup = BeautifulSoup(hltvHTML, 'html.parser')

    hltvMatches = hltvSoup.select("#back > div.mainAreaNoHeadline > div.centerNoHeadline > div > div.covMainBoxContent > div > div > div")[5:]
    hltvMatchesFormatted = [formatMatch(hltvMatch) for hltvMatch in hltvMatches]
    hltvMatchesFiltered = [x for x in hltvMatchesFormatted if x is not None]

    return hltvMatchesFiltered

# writes lists to file
def writeMatchesToFile(matchesOfPage, maxMatch):
    with open('hltv_matches.csv', 'ab') as csvfile:
        hltvWriter = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for match in matchesOfPage:
            if int(match[1]) <= int(maxMatch):
                return False
            hltvWriter.writerow(match)
    return True

maxMatch = -1
found = []
if os.path.exists('hltv_matches.csv'):
    with open('hltv_matches.csv', 'rb') as csvfile:
        hltvReader = unicodecsv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for row in hltvReader:
            found += [row['matchid']]
            if int(row['matchid']) > int(maxMatch):
                maxMatch = row['matchid']
else:
    with open('hltv_matches.csv', 'ab') as csvfile:
        hltvWriter = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        hltvWriter.writerow(["date", "matchid", "teamid1", "teamid2", "eventid", "score1", "score2",
            "team1player1id", "team1player2id", "team1player3id", "team1player4id", "team1player5id", "team2player1id", "team2player2id", "team2player3id", "team2player4id", "team2player5id", "map", "team1name", "team2name", "match"])

print 'Scanning matches until %s' % maxMatch

i = 0
while True:
    hltvUrlbase = 'http://www.hltv.org/?pageid=188&statsfilter=0&offset='
    hltvUrlOffset = str(i)
    hltvUrl = hltvUrlbase + hltvUrlOffset
    matchesOfPage = getMatchesOfPage(hltvUrl)
    if(len(matchesOfPage)):
        if not writeMatchesToFile(matchesOfPage, maxMatch):
            break
        print strftime("%Y-%m-%d %H:%M:%S: ", gmtime()) + str(len(matchesOfPage)) + " HLTV CS:GO matches completed."
    else:
        break
    i += 50
