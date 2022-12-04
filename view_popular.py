import webbrowser
from pathlib import Path
import json

users = []
path = Path('sorted_mastodon_users.txt')
with open(path) as f:
    for line in f:
        users.append(json.loads(line))


counter = 0
for user in users[:1000]:
    counter += 1
    webbrowser.open(user['url'])
    if not (counter % 10):
        r = input('Continue? [y/n]').lower()
        if r == 'n':
            break