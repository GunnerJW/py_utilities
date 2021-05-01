import os
from multiprocessing.dummy import Pool as ThreadPool

import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict

__author__ = 'GunnerJW'

# Insert you Kattis login cookies here
COOKIES = {}

# Insert the path of the folder where you want the files dumped here
DUMP_PATH = r'C:\Users\T480\Kattis-Solutions'

# Insert the URL of the Kattis user page here
KATTIS_USER_URL = 'https://open.kattis.com/users/user'


def get_submissions():
    res = defaultdict(dict)

    page_number = 0
    while True:
        response = requests.get(
            KATTIS_USER_URL,
            cookies=COOKIES,
            params={'page': page_number} if page_number > 0 else None
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        submissions_table_body = soup.find('table', {'class': 'table-submissions'}).tbody
        rows = submissions_table_body.find_all('tr')
        if len(rows) == 0:
            break
        for row in rows:
            cells = row.find_all('td')

            status = cells[3].text
            if status != 'Accepted':
                continue

            submission_id = cells[0].text
            submission_date = pd.Timestamp(cells[1].text.strip())
            problem = cells[2].text
            execution_time_in_seconds = float(cells[4].text[:-2])
            language = cells[5].text

            if problem in res and language in res[problem]:
                _, _, previous_submission_date, previous_execution_time_in_seconds = res[problem][language]
                if execution_time_in_seconds < previous_execution_time_in_seconds:
                    # Choose the more performant submission
                    res[problem][language] = (problem, submission_id, submission_date, execution_time_in_seconds)
                elif execution_time_in_seconds == previous_execution_time_in_seconds:
                    if submission_date > previous_submission_date:
                        # Choose the more recent submission, since there are high chances its code will be of higher quality
                        res[problem][language] = (problem, submission_id, submission_date, execution_time_in_seconds)
            else:
                res[problem][language] = (problem, submission_id, submission_date, execution_time_in_seconds)

        page_number += 1

    return res


def get_submission_page(submission_id):
    response = requests.get(
        f'https://open.kattis.com/submissions/{submission_id}',
        cookies=COOKIES
    )
    return response


def get_codes(submissions):
    res = defaultdict(dict)
    submissions_ids = [
        submission[1]
        for submissions_by_language in submissions.values()
        for submission in submissions_by_language.values()
    ]
    with ThreadPool(20) as pool:
        http_responses = dict(zip(submissions_ids, pool.map(get_submission_page, submissions_ids)))

    for problem in submissions:
        for language in submissions[problem]:
            problem, submission_id, submission_date, execution_time_in_seconds = submissions[problem][language]
            response = http_responses[submission_id]

            soup = BeautifulSoup(response.content, 'html.parser')
            submission_code_container = soup.find('div', {'class': 'submission_code_container'})
            source_code = submission_code_container.find('div', {'class': 'source-highlight'}).text
            problem_url = soup.find('td', {'id': 'problem_title'}).a['href']
            problem_link = 'https://open.kattis.com' + problem_url
            filename = submission_code_container.h3.text
            if language == 'Java':
                filename = f'{problem_url.split("/")[-1]}.java'
            comment_delimiter_start = '/*'
            comment_delimiter_end = '*/'
            if language.startswith('Python'):
                comment_delimiter_start = '"""'
                comment_delimiter_end = '"""'

            prefaced_source_code = f'{comment_delimiter_start}\n'
            prefaced_source_code += f'{language} solution for the problem {problem} ({problem_link})\n'
            prefaced_source_code += f'Execution time: {execution_time_in_seconds} s\n'
            prefaced_source_code += f'Submitted on {submission_date}\n'
            prefaced_source_code += f'Source code extracted automatically by the script ' \
                                    f'https://github.com/GunnerJW/py_utilities/blob/master/' \
                                    f'kattis_solved_problems_code_extract.py\n'
            prefaced_source_code += f'{comment_delimiter_end}\n\n'
            prefaced_source_code += source_code

            res[problem][language] = (filename, prefaced_source_code)

    return res


def dump_source_codes(codes_dict):
    for problem in codes_dict:
        for language in codes_dict[problem]:
            filename, source_code = codes_dict[problem][language]
            with open(os.path.join(DUMP_PATH, filename), 'wb') as f:
                f.write(source_code.encode('utf-8'))


if __name__ == '__main__':
    submissions = get_submissions()
    codes = get_codes(submissions)
    dump_source_codes(codes)
