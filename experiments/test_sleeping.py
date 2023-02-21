import requests
import httpx


chrome_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
                                ' (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                  'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive'}
print(chrome_headers)

# url = 'https://sleeping.town/api/v1/instance/peers'
url = 'http://httpbin.org/headers'
print('Making request with headers set as chrome...')

r = requests.get(url, headers=chrome_headers, timeout=3.5)
out = r.json()
print(f'requests: {out}')

print('Making request with default headers:')
r = requests.get(url, timeout=3.5)  # never response, not exception, no time out...
out = r.json()
print(f'requests: {out}')

print('Making request with default headers:')
r = httpx.get(url, timeout=3.5)
out = r.json()
print(f'httpx: {out}')
