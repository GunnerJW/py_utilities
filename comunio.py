"""
This script scraps the evolution graphs of football players in the Club Comunio Premier League website (https://premier.clubcomunio.com/).
The targeted player URL should be put in the variable PLAYER_URL.
The result is a pandas Series object, whose index is the X-axis of the graph, representing dates, and whose values
are the Y-axis of the graph.
"""
from ast import literal_eval

import requests
from bs4 import BeautifulSoup
import pandas as pd
import dateparser

PLAYER_URL = 'https://premier.clubcomunio.com/jugador/thomas-p'

response = requests.get(PLAYER_URL)
content = response.text
soup = BeautifulSoup(content, 'html.parser')
script_tags = soup.find_all('script')
chart_script = script_tags[6]
javascript_text = chart_script.contents[0]
dates_list = []
values_list = []
for line in javascript_text.split('\n'):
    line = line.strip()
    if line.startswith('var _labels'):
        current_year = pd.Timestamp('today').year
        dates_list = literal_eval(line.split(' = ')[1][:-1])
        dates_list = list(map(lambda dt: f'{dt} {current_year}', dates_list))
        dates_list = list(map(lambda dt: dateparser.parse(dt), dates_list))
    elif line.startswith('var _data'):
        values_list = [value // 1000 for value in literal_eval(line.split(' = ')[1][:-1])]

serie = pd.Series(data=values_list, index=dates_list)