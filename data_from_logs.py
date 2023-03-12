from pathlib import Path
from datetime import datetime
from pprint import pprint

"""
Parse log files and generate stats

Sample Log file format:
INFO | 2023-03-11 10:01:33 | almere_social | 11 unique records
INFO | 2023-03-11 10:01:35 | almere_social | 11 unique records
INFO | 2023-03-11 10:01:35 | almere_social | All Data Returned

# to do - why is the log converting alemer.social to almere_social?
"""


def number_of_records(log_lines):
    try:
        n = int(log_lines[-2].split('|')[3].split()[0])
    except ValueError:
        n = 0
    return n

def duration(log_lines):
    # get start and end time from log, return the duration as a timedelta
    # get start time from lines [0], end time for log_lines[-1]
    start_str = log_lines[0].split('|')[1].strip()
    start = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
    end_str = log_lines[-1].split('|')[1].strip()
    end = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
    return end - start

def domain(log_lines):
    return log_lines[0].split('|')[2].strip()


error_response = 0
zero_records = 0
responding_servers = 0
stats = []
p = Path('log')
for fn in p.glob('*.*'):
    with open(fn) as f:
        lines = f.read().splitlines()
    if len(lines) == 1:
        error_response += 1
    elif number_of_records(lines)  == 0:
        zero_records += 1
    else:
        responding_servers += 1
        stats.append([domain(lines), number_of_records(lines),duration(lines)])
stats.sort(key=lambda x: x[1], reverse=True)
pprint(stats[:20])

pprint(stats[-20:])






print(f'Servers that respond with an error: {error_response}')
print(f'Servers that respond with zero records: {zero_records}')
print(f'Servers Responding with at least 1 user record: {responding_servers}')