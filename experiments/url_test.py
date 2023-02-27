from urllib.parse import urlparse, urlunparse
import requests
import httpx
from pprint import pprint
import os

try:
    headers = {'user_agent': os.environ['user_agent']}
except KeyError:
    headers = {}

# url = 'https://🍺🌯.to/api/v1/instance/peers'
# url = 'https://sleeping.town/api/v1/instance/peers'
url = 'https://az.social/api/v1/instance'



# converted_url = convert_idna_address(url)
# print(f'{url=} {converted_url=}')

r = requests.get(url, headers=headers, timeout=3.5)
out = r.json()
# print(f'requests: {out}')
print(r.request.headers)

r = httpx.get(url, headers=headers, timeout=3.5)
out = r.json()
# print(f'httpx: {out}')
print(r.request.headers)