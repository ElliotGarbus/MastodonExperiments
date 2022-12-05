import json
from pathlib import Path

in_path = Path('mastodon_users.txt')
out_path = Path('user.csv')

unique_urls = set()
with open(in_path) as in_file, open(out_path, 'w') as out_file:
    for line in in_file:
        user = json.loads(line)
        if user['url'] in unique_urls:
            continue
        unique_urls.add(user['url'])
        out_file.write(f"{user['followers_count']}\n")
