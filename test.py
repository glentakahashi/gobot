#!/usr/local/bin/python
from collections import deque
import argparse
import urllib2
from bs4 import BeautifulSoup
import re
import csv
from time import gmtime, strftime
import unicodecsv

import sqlite3
conn = sqlite3.connect('betting.db')

#hltv -> csgolounge
mappings = {
        'complexity': 'col',
        'cph wolves': 'cw',
        'ibuypower': 'ibp',
        'e-frag.net': 'e-frag',
        'flipsid3': 'fsid3',
        'hellraisers': 'hr',
        'ldlc white': 'ldlc.white',
        'luminosity': 'lg',
        'mousesports': 'mouz',
        'clan-mystik': 'mystik',
        'natus vincere': "na'vi",
        'enemy': 'nme',
        'publiclir.se': 'publiclir',
        'space soldiers': 'spaces',
        'vega squadron': 'vega',
        'virtus.pro': 'vp'
    }

c = conn.cursor()

# Create table
c.execute('''drop table if exists ratings''')
c.execute('''CREATE TABLE ratings (date text, team text, rating real)''')

# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()

#create the database of gliphs
with open('data/hltv.csv'%site, 'rb') as csvfile:
    reader = unicodecsv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    for
