from pathlib import Path
import json
from pprint import pprint
import webbrowser


users = []
path = Path('hachyderm_io_users.txt')
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

