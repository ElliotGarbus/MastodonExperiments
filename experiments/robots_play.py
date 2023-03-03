from urllib.robotparser import RobotFileParser
import json

import requests

with open('../seed_instances.json') as f:
    sites = json.load(f)

# sites = ["mastodon.social", "mastodon.world", "az.social", "mas.to", "mastodon.lol", "techhub.social", "universeodon.com"]
print(f'Number of sites: {len(sites)}')

for site in sites:
    robot_url = f'https://{site}/robots.txt'
    rp = RobotFileParser(url=robot_url)
    try:
        r = requests.get(robot_url)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        # print(f'{site} network error')
        continue
    rp.parse(r.text.splitlines())
    if not rp.can_fetch("MyCrawler", "/api/"):
        print(f'{site} can not access the api')
        print(r.text)

# for site in sites:
#     robot_url = f'https://{site}/robots.txt'
#     rp = RobotFileParser(url=robot_url)
#     # r = requests.get(robot_url)
#     rp.read()
#     # rp.parse(r.text.splitlines())
#     print(f'{site}: {rp.can_fetch("MyCrawler", "/api/")=}')
#     print(f'{site}: {rp.can_fetch("MyCrawler", "/media_proxy/")=}')
