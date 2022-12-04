# remove duplicate line items from a file of mastodon dir entries

from pathlib import Path
import json
from pprint import pprint

in_path = Path('mastodon_users.txt')
clean_path = Path('clean_mastodon_users.txt')
sorted_path = Path('sorted_mastodon_users.txt')

unique_urls = set()
line_count = 0
with open(in_path) as in_file, open(clean_path, 'w') as out_file:
    for line in in_file:
        line_count += 1
        user = json.loads(line)
        if user['url'] in unique_urls:
            continue
        unique_urls.add(user['url'])
        out_file.write(line)

dups = line_count - len(unique_urls)
print(f'{line_count=}  {len(unique_urls)=}  {dups} duplicates removed ')
# now sort cleaned file...
users = []
with open(clean_path) as clean_file:
    for line in clean_file:
        users.append(json.loads(line))

sorted_users = sorted(users, key=lambda x: int(x['followers_count']), reverse=True)
with open(sorted_path, 'w') as sorted_file:
    for user in sorted_users[1:]:
        sorted_file.write(json.dumps(user) + '\n')
        

line_count = 1
for user in sorted_users[1:1000]:
    print(f"{line_count}  url: {user['url']}, 'followers:' {user['followers_count']}")
    line_count += 1

