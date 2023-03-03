from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import json

import requests

rp = RobotFileParser()
rp.set_url('https://az.social/robots.txt')
rp.read()
print(f'{rp.can_fetch("*","/api")=}')
print(f'{rp.can_fetch("my crawler", "/media_proxy/")=}')

# with open('../seed_instances.json') as f:
#     sites = json.load(f)

sites = ["mastodon.social", "mastodon.world", "mas.to", "mastodon.lol", "techhub.social",
         "universeodon.com", 'www.musi-cal.com']

for site in sites:
    robot_url = f'https://{site}'
    rp = RobotFileParser()
    rp.set_url(robot_url)
    rp.read()
    print(f'{site} {rp.can_fetch("my crawler", "https://{site}/api/")=}')
    print(f'{site} {rp.can_fetch("my crawler", "https://{site}/media_proxy/")=}')





