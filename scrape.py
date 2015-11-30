#!/usr/local/bin/python
import argparse
import urllib2
from bs4 import BeautifulSoup
import re
import csv
from time import gmtime, strftime
import unicodecsv

parser = argparse.ArgumentParser(description='Scrape one of the ___lounge.com sites.')
parser.add_argument('site', metavar='site', type=str, help='which site to parse, either dota2lounge or csgolounge')

args = parser.parse_args()
site = args.site

LOUNGE_URL = "http://%slounge.com/"%site

csgocurrent = 7473
dota2current = 10499

current = 0

if site == 'csgo':
    current = csgocurrent
elif site == 'dota2':
    current = dota2current

def getMatch(url, i):
    req = urllib2.Request(url + str(i), headers={'User-Agent' : "scraping bot"})
    con = urllib2.urlopen(req)
    print(url + str(i) + " " + str(con.getcode()))
    html = con.read()
    soup = BeautifulSoup(html, 'html.parser')
    if len(soup.select("body > main > section > h1")) > 0 and soup.select("body > main > section > h1")[0].text == '404':
        print ("404, matchid = " + str(i))
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
    if 'class' not in status or 'full' in status['class']:
        status = ""
    else:
        status = status.text
    winner = "a" if team_a_won else "b" if team_b_won else "none"

    with open('%s.csv'%site, 'ab') as csvfile:
        writer = unicodecsv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([i, date, bo, team_a, team_b, team_a_pct, team_b_pct, team_a_odds, team_b_odds, winner, status])

# loops over pages (-> 8800 all matches in 2014 & 2015 at 27.11.2015)
for i in range(1,current+1):
    url = LOUNGE_URL + "match?m="
    getMatch(url, i)
    #writeMatchesToFile(matchesOfPage, i)
    #print strftime("%Y-%m-%d %H:%M:%S: ", gmtime()) + str(i + 50) + " HLTV CS:GO matches completed."
