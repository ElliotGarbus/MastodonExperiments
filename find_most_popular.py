import argparse
import json
import webbrowser


parser = argparse.ArgumentParser(description='Review the 100 most followed users, 10 at a time.')
parser.add_argument('filename', help='file of mastodon directory records')
args = parser.parse_args()

users = []
with open(args.filename) as f:
    for line in f:
        d = json.loads(line)
        users.append({'url': d['url'], 'followers': int(d['followers_count'])})
top_100 = sorted(users, key=lambda x: x['followers'], reverse=True)[:100]

counter = 0
for user in top_100:
    counter += 1
    webbrowser.open(user['url'])
    if not (counter % 10):
        r = input('Continue? [y/n]').lower()
        if r == 'n':
            break

