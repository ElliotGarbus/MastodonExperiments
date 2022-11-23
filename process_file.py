from pathlib import Path
from pprint import pprint

path = Path('mastodon_users.txt')

with open(path) as f:
    line = f.readline()

pprint(line)
