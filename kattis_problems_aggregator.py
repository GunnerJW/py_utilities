"""
    This script parses the content of URLs 1* and 2** and then aggregates the kattis problems into an Excel spreadsheet

    *: http://torstein.stromme.me/kattis/
    **: https://cpbook.net/methodstosolve?oj=kattis&topic=all&quality=all
"""
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup

DUMP_PATH = os.path.join(os.getenv('HOMEPATH'), 'Kattis problems.xlsx')


def text_to_hyperlink(text, url):
    return f'=HYPERLINK("{url}"; "{text}")'


def problem_id_to_url(pb_id):
    return f'https://open.kattis.com/problems/{pb_id}'


html = requests.get('https://cpbook.net/methodstosolve?oj=kattis&topic=all&quality=all').content
soup = BeautifulSoup(html, 'html.parser')

table_body = soup.find('div', {'class': 'row'}).table.tbody
rows = table_body.find_all('tr')

dict_ = {
    'Kattis ID': [],
    'Topic': [],
    'Hint': []
}

for row in rows:
    cells = row.find_all('td')
    problem_url = cells[1].a['href']
    dict_['Kattis ID'].append(text_to_hyperlink(cells[0].text, problem_url))
    dict_['Topic'].append(cells[2].text)
    dict_['Hint'].append(cells[3].text)

html2 = requests.get('http://torstein.stromme.me/kattis/').content
soup2 = BeautifulSoup(html2, 'html.parser')

table_body2 = soup2.find('table', {'id': 'myTable'}).tbody
rows2 = table_body2.find_all('tr')

for row in rows2:
    cells = row.find_all('td')
    problem_id = cells[0].text
    problem_url = problem_id_to_url(problem_id)
    dict_['Kattis ID'].append(text_to_hyperlink(problem_id, problem_url))
    dict_['Topic'].append(cells[3].text)
    dict_['Hint'].append('')

pd.DataFrame(dict_).to_excel(DUMP_PATH, index=False)
