from urllib.robotparser import RobotFileParser
import json

import requests

rp = RobotFileParser()
rp.set_url('https://az.social/robots.txt')
rp.read()
print(f'{rp.can_fetch("*","https://az.social/api")=}')
# print(f'{rp.crawl_delay("*")=}')
# print(f'{rp.mtime()=}')

# with open('../seed_instances.json') as f:
#     sites = json.load(f)

sites = ["mastodon.social", "mastodon.world", "mas.to", "mastodon.lol", "techhub.social", "universeodon.com"]

for site in sites:
    robot_url = f'https://{site}/robots.txt'
    rp.set_url(robot_url)
    rp.read()
    url = f"https://{site}"
    print(f' {url} {rp.can_fetch("*", url)=}')

for site in sites:
    robot_url = f'https://{site}/robots.txt'
    r = requests.get(robot_url)
    print(robot_url)
    print(r.text)


