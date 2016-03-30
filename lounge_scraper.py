#!/usr/local/bin/python
from collections import deque
import argparse
import urllib2
from bs4 import BeautifulSoup
import os
import re
import csv
from time import gmtime, strftime
import unicodecsv

parser = argparse.ArgumentParser(description='Scrape one of the ___lounge.com sites.')
parser.add_argument('site', metavar='site', type=str, help='which site to parse, either dota2lounge or csgolounge')
parser.add_argument('--retry-failed', type=bool, metavar='failed', help='retry failed')

args = parser.parse_args()
site = args.site
csvpath = '%s_lounge.csv'%site

LOUNGE_URL = "http://%slounge.com/"%site

current = 0

req = urllib2.Request(LOUNGE_URL, headers={'User-Agent' : "scraping bot"})
con = urllib2.urlopen(req)
html = con.read()
soup = BeautifulSoup(html, 'html.parser')
matches = soup.select("div.match > div > a")
for match in matches:
    match = int(re.findall(r'\d+', match['href'])[0])
    if match > current:
        current = match

def getMatch(url, i):
    req = urllib2.Request(url + str(i), headers={'User-Agent' : "scraping bot"})
    con = urllib2.urlopen(req)
    print(url + str(i) + " " + str(con.getcode()))
    html = con.read()
    soup = BeautifulSoup(html, 'html.parser')
    if len(soup.select("body > main > section > h1")) > 0 and soup.select("body > main > section > h1")[0].text == '404':
        print ("404, matchid = " + str(i))
        with open(csvpath, 'ab') as csvfile:
            writer = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow([i, "404"])
        return
    date = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > div:nth-of-type(1) > div:nth-of-type(3)")[0]
    date = date['title'] + " " + date.text.strip()
    bo = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > div:nth-of-type(1) > div:nth-of-type(2)")[0].text
    team_a = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > a:nth-of-type(1) > span > b")[0].text
    team_b = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > a:nth-of-type(2) > span > b")[0].text
    team_a_pct = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > a:nth-of-type(1) > span")[0].i.text
    team_b_pct = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > a:nth-of-type(2) > span")[0].i.text
    team_a_odds = re.findall(r'(\d+(\.\d+)? (to \d+(\.\d+)? )?for 1)',str(soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > div.full")[0].select('div.half')[0].find('div')))[0][0]
    team_b_odds = re.findall(r'(\d+(\.\d+)? (to \d+(\.\d+)? )?for 1)',str(soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > div.full")[0].select('div.half')[1].find('div')))[0][0]
    team_a_won = "(win)" in team_a.lower()
    team_b_won = "(win)" in team_b.lower()
    status = soup.select("body > main > section:nth-of-type(1) > div.box-shiny-alt > div:nth-of-type(2)")[0]
    if status.has_attr('class') and 'full' in status['class']:
        status = ""
    else:
        status = status.text.strip()
    winner = "a" if team_a_won else "b" if team_b_won else "none"

    with open(csvpath, 'ab') as csvfile:
        writer = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([i, date, bo, team_a, team_b, team_a_pct, team_b_pct, team_a_odds, team_b_odds, winner, status])

start = 1
url = LOUNGE_URL + "match?m="

if os.path.exists(csvpath):
    with open(csvpath, 'rb') as csvfile:
        reader = unicodecsv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        start = int(deque(reader,1)[0][0])+1
else:
    start = 1

print "Last match we have is %s" % start
print "Current match is %s" % current

if args.retry_failed:
    with open(csvpath, 'rb') as csvfile:
        reader = unicodecsv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            if row[1] == 'failed' or row[1] == '404':
                try:
                    getMatch(url,int(row[0]))
                except Exception as e:
                    print "%s still failed"%row[0]
else:
    for i in range(start,current+1):
        try:
            getMatch(url, i)
        except Exception as e:
            print(str(i) +  " failed parsing")
            with open(csvpath, 'ab') as csvfile:
                writer = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([i, "failed"])
        #writeMatchesToFile(matchesOfPage, i)
        #print strftime("%Y-%m-%d %H:%M:%S: ", gmtime()) + str(i + 50) + " HLTV CS:GO matches completed."
