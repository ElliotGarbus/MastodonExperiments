# visit all known instances, identify new peers, and scan for new instances
# synchomous version to work around an httpx bug
"""
start with a file that contains a list of know instances, and a set that contains the known instances
for each instance get its peers
find the peers that are not known, put them in the unknown set.
add the unknows to the know set
for each unknown, get the peers
repeat until there are no unknowns in this "thread"
when complete update know and write the file
"""


import json
import logging
# import warnings
from urllib.parse import urlparse, urlunparse

import requests

# import httpx
# import trio
# from tenacity import (AsyncRetrying, stop_after_attempt, TryAgain, wait_fixed, after_log,
#                       retry_if_exception_type, RetryError)
# from trio import TrioDeprecationWarning
#
# # turn off deprecation warning issue with a httpx dependency, anyio
# warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

def convert_idna_address(url: str) -> str:
    parsed_url = urlparse(url)
    return urlunparse(parsed_url._replace(netloc=parsed_url.netloc.encode("idna").decode("ascii")))


def get_peers(name):
    print(f'Get peers from {name} ')
    url = convert_idna_address(f"https://{name}/api/v1/instance/peers")
    # properly encode urls that have emoji characters or other unicode
    # url = f"https://{name}/api/v1/instance/peers"
    # print(f'{url=}')
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f'JSON Error: {e}')
        return []
    except requests.exceptions.HTTPError as e:
        logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        return []
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout, requests.exceptions.TooManyRedirects) as e:
        logging.exception(f'{name} {url} {e}')
        print(f'{url} {name} {e}')
        return []
    except Exception as e:
        logging.exception(f'{name} {url} {e}')
        print(f'{url} {name} {e}')
        raise e

def write_data(instance, peers):
    data = {instance: peers}
    with open('graph.txt', 'a') as f:
        s = json.dumps(data)
        f.write(s + '\n')
    with open('mastodon_instances.txt', 'a') as f:
        f.write(instance.encode('unicode_escape').decode() + '\n')


def crawl_peers(name, known):
    """
    get peers, if peers are not on the know list, scan to read their peers
    repeat crawling down the peers - until all are known
    """
    peers = get_peers(name)
    peers = [x for x in peers if not any([x.endswith('activitypub-troll.cf'), x.endswith('misskey-forkbomb.cf'),
                                          x.endswith('repl.co')])]
    write_data(name, peers)
    discovered = set()  # hold discovered instances
    unknown = set(peers) - known
    discovered.update(unknown)
    while unknown:
        instance = unknown.pop()
        known.add(instance)
        peers = get_peers(instance)
        peers = [x for x in peers if not any([x.endswith('activitypub-troll.cf'), x.endswith('misskey-forkbomb.cf'),
                                              x.endswith('repl.co')])]
        write_data(instance, peers)
        new_unknown_peers = set(peers) - known
        unknown.update(new_unknown_peers)
        discovered.update(new_unknown_peers)
        print(f'{instance} Number of peers: {len(peers)}; Number unknown {len(unknown)}')


def main():
    logging.basicConfig(filename='rootlog.log', level=logging.DEBUG)
    # with open('mastodon_instances.txt') as f:  # todo: add exception handling
    #     instances = json.load(f)

    instances = ['🍺🌯.to']

    known = set(instances)
    for mi in instances:
        crawl_peers(mi, known)
    with open('out_mastodon_instances.txt', 'w') as f:
        json.dump(list(known), f)
    print('Done!')


if __name__ == '__main__':
    # with keepawake(keep_screen_awake=False):
    # trio.run(main)
    main()