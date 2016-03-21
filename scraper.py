#!/usr/local/bin/python
# scrape HLTV results for CS:GO Matches

# get website content
import urllib2
from bs4 import BeautifulSoup
import re
import csv
from time import gmtime, strftime
import unicodecsv

# extract match information and format to list
def formatMatch(hltvMatch):
   hltvMatchNames = hltvMatch.get_text(";", strip = True)
   hltvMatchScore = re.findall('\((\d*?)\)', hltvMatchNames)
   hltvMatchIds = [re.search('(teamid|matchid|eventid)=?(\d*)', link.get('href')).group(2) for link in hltvMatch.select("a")]
   hltvMatchLine = hltvMatchNames.split(';') + hltvMatchIds + hltvMatchScore
   return hltvMatchLine

# gets all matches from one page
def getMatchesOfPage(hltvUrl):
   hltvReq = urllib2.Request(hltvUrl, headers={'User-Agent' : "github users please insert something meaningful here"})
   hltvCon = urllib2.urlopen(hltvReq)
   hltvHTML = hltvCon.read()
   hltvSoup = BeautifulSoup(hltvHTML, 'html.parser')

   hltvMatches = hltvSoup.select("#back > div.mainAreaNoHeadline > div.centerNoHeadline > div > div.covMainBoxContent > div > div > div")[5:]
   hltvMatchesFormatted = [formatMatch(hltvMatch) for hltvMatch in hltvMatches]

   return hltvMatchesFormatted

# writes lists to file
def writeMatchesToFile(matchesOfPage, iteration):
   with open('hltv_org_matches_2014.csv', 'ab') as csvfile:
      hltvWriter = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
      if iteration == 0:
         hltvWriter.writerow(["date", "team1", "team2", "map", "event", "matchid", "teamid1", "teamid2", "eventid", "score1", "score2"])
      for match in matchesOfPage:
         hltvWriter.writerow(match)

# loops over pages (-> 8800 all matches in 2014 & 2015 at 27.11.2015)
for i in range(0, 14000, 50):
   hltvUrlbase = 'http://www.hltv.org/?pageid=188&statsfilter=0&offset='
   hltvUrlOffset = str(i)
   hltvUrl = hltvUrlbase + hltvUrlOffset
   matchesOfPage = getMatchesOfPage(hltvUrl)
   writeMatchesToFile(matchesOfPage, i)
   print strftime("%Y-%m-%d %H:%M:%S: ", gmtime()) + str(i + 50) + " HLTV CS:GO matches completed."







