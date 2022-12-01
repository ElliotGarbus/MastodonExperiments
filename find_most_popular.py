from pathlib import Path
import json
from pprint import pprint


users = []
path = Path('mastodon_users.txt')
with open(path) as f:
    for line in f:
        d = json.loads(line)
        users.append({'url': d['url'], 'followers': int(d['followers_count'])})

pprint(sorted(users, key=lambda x: x['followers'], reverse=True)[:100])
