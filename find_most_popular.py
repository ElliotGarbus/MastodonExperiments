from pathlib import Path
import json
from pprint import pprint

def sort_key(s):
    keyword = 'followers: '
    start = s.find(keyword) + len(keyword)
    return int(s[start:])

users = []
unique_users = set()
path = Path('mastodon_users.txt')
with open(path) as f:
    for line in f:
        if not line.startswith('\"error\"'):
            d = json.loads(line)
            unique_users.add(f"{d['url']} followers: {d['followers_count']}")
    for user in unique_users:
        users.append(user)

pprint(sorted(users, key=sort_key, reverse=True)[:100])