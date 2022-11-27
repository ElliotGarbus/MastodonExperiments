from pathlib import Path
import json
from collections import Counter

path = Path('mastodon_users.txt')
line_count = 0
count = Counter()
with open(path) as f:
    for line in f:
        line_count += 1
        # print(line)
        if not line.startswith('\"error\"'):
            d = json.loads(line)
            count[d['url']] += 1

        # print(f"{d['url']} followers: {d['followers_count']}")
print(f'{line_count=}')
print(count)


