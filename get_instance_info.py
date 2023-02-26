import json
import logging
import warnings
from pathlib import Path

import httpx
import requests
import trio
from idna.core import InvalidCodepoint

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=trio.TrioDeprecationWarning)

INSTANCE_API_VERSION = 'v1'

def get_info_sync(url):
    """
    This function is a work-around for a bug in httpx.  Httpx does not work properly with emoji in the url
    fall back to requests if an invalid code point is detected (emoji in url)
    :param url:
    :return: list of peers
    """
    print(f'Get info from {url} ')
    # properly encode urls that have emoji characters or other unicode
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f'JSON Error: {e} {r.text}')
        return None
    except requests.exceptions.HTTPError as e:
        logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        return None
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout, requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError, requests.exceptions.InvalidURL,
            requests.exceptions.InvalidSchema) as e:
        logging.exception(f'{url} {e}')
        print(f'{url} {e}')
        return None
    except Exception as e:
        logging.exception(f'{url} {e}')
        print(f'{url}  {e}')
        return None


async def get_info(name):
    print(f'Get info from {name} ')
    url = f"https://{name}/api/{INSTANCE_API_VERSION}/instance"
    # properly encode urls that have emoji characters or other unicode
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except json.JSONDecodeError as e:
            logging.error(f'JSON Error: {e} {r.text}')
            return None
        except httpx.HTTPStatusError as e:
            logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
            return None
        except httpx.RequestError as e:
            logging.error(f'Connection Error {e} on {url}')
            return None
        except InvalidCodepoint as e:
            print(f'Invalid URL: {url}')
            logging.error(f'{e} {url}')
            return get_info_sync(url)
        except Exception as e:
            logging.exception(f'{name} {url} {e}')
            print(f'UNKNOWN EXCEPTION: {url} {name} {e}')
            raise e


def is_info_valid(info):
    """
    Tests if the info data returned from a server is valid
    :param info: The info dict from a server
    :return: True if the data is valid
    """
    if INSTANCE_API_VERSION == 'v1':
        valid = (info and
                 'stats' in info and
                 isinstance(info['stats']['user_count'], int) and
                 info['stats']['user_count'] and
                 isinstance(info['uri'], str))
    elif INSTANCE_API_VERSION == 'v2':
        valid = (info and 'domain' in info)
    else:
        raise ValueError(f'Invalid value {INSTANCE_API_VERSION} for INSTANCE_API_VERSION')
    return valid


def clean_uri(info):
    """
    removes the leading https:// for the uri field, only a small number of servers include this prefix
    makes the uri data consistent across all servers
    :param info: The info dict from a server
    :return: None, modifies data in place
    """
    if INSTANCE_API_VERSION == 'v1':
        info['uri'] = info['uri'].replace('https://', '')
    elif INSTANCE_API_VERSION == 'v2':
        pass
    else:
        raise ValueError(f'Invalid value {INSTANCE_API_VERSION} for INSTANCE_API_VERSION')


async def get_info_task(instances, outfile):
    while instances:
        name = instances.pop()
        info = await get_info(name)
        if is_info_valid(info):
            clean_uri(info)
            with open(outfile, 'a') as f:
                json.dump(info, f)
                f.write('\n')


async def main():
    logfile = Path('get_instance_info.log')
    logfile.unlink(missing_ok=True)
    logging.basicConfig(filename=logfile, level=logging.ERROR)

    outfile = Path('instance_info.txt')
    outfile.unlink(missing_ok=True)

    with open('mastodon_instances.txt') as f:
        instances = f.read().splitlines()

    async with trio.open_nursery() as nursery:
        for x in range(500):
            nursery.start_soon(get_info_task, instances, outfile)


if __name__ == '__main__':
    trio.run(main)
