import json
from pprint import pprint

with open('../results/mastodon_cloud.txt') as f:
    data = [json.loads(x) for x in f.read().splitlines()]
pprint(data[0])

bots = [1 for x in data if x['bot'] is True and not x['followers_count']]
print(f'{sum(bots)=}')
