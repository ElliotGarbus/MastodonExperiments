from pathlib import Path
import json
from pprint import pprint
import webbrowser
import sys


users = []
try:
    file = sys.argv[1]
except IndexError:
    raise ValueError('No file argument')

path = Path(file)
with open(path) as f:
    for line in f:
        d = json.loads(line)
        users.append({'url': d['url'], 'followers': int(d['followers_count'])})
top_100 = sorted(users, key=lambda x: x['followers'], reverse=True)[:100]
pprint(top_100)

counter = 0
for user in top_100:
    counter += 1
    webbrowser.open(user['url'])
    if not (counter % 10):
        r = input('Continue? [y/n]').lower()
        if r == 'n':
            break

