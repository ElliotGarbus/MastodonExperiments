from urllib.parse import urlparse, urlunparse
import requests
import httpx

def convert_idna_address(url: str) -> str:
    parsed_url = urlparse(url)
    return urlunparse(
        parsed_url._replace(netloc=parsed_url.netloc.encode("idna").decode("ascii"))
    )


# url = 'https://🍺🌯.to/api/v1/instance/peers'
url = 'https://sleeping.town/api/v1/instance/peers'
converted_url = convert_idna_address(url)
print(f'{url=} {converted_url=}')

r = requests.get(converted_url, timeout=(3.5, 3.5))
out = r.json()
print(f'requests: {out}')

# r = httpx.get(converted_url, timeout=3.5)
# out = r.json()
# print(f'httpx: {out}')