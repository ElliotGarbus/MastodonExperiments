from pathlib import Path
import json

path = Path('saved/mastodon_users.txt')

with open(path) as f:
    for line in f:
        d = json.loads(line)
        print(f"{d['url']} followers: {d['followers_count']}")

