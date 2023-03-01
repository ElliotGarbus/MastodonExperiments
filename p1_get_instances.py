# visit instances, identify new peers, and scan for new instances

"""
start with a file that contains a list of know instances, convert to a set called unknown
for each instance get its peers, once scanned add that instance to the know set
find the peers that are not known, put them in the unknown set.
for each unknown, get the peers
repeat until there are no unknowns in this "task"
"""

import json
import logging
from pathlib import Path
import warnings
from urllib.parse import urlparse, urlunparse

import httpx
from idna.core import InvalidCodepoint
import requests
import trio
from trio import TrioDeprecationWarning
from wakepy import keepawake

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

# some flags to control execution, do not expect them to be used
from flags import IGNORE_EMOJI_URL, CREATE_GRAPH, user_agent_header


def convert_idna_address(url: str) -> str:
    parsed_url = urlparse(url)
    return urlunparse(parsed_url._replace(netloc=parsed_url.netloc.encode("idna").decode("ascii")))


def get_peers_sync(url):
    """
    This function is a work-around for a bug in httpx.  Httpx does not work properly with emoji in the url
    fall back to requests if an invalid code point is detected (emoji in url)
    :param url:
    :return: list of peers
    """
    print(f'Get peers from {url} ')
    try:
        r = requests.get(url, headers=user_agent_header, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f'JSON Error: {e}')
        return []
    except requests.exceptions.HTTPError as e:
        logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        return []
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout, requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError, requests.exceptions.InvalidURL,
            requests.exceptions.InvalidSchema) as e:
        logging.exception(f'{url} {e}')
        print(f'{url} {e}')
        return []
    except Exception as e:
        logging.exception(f'UNKNOWN EXCEPTION{url} {e}')
        print(f'{url}  {e}')
        return []


async def get_peers(name):
    print(f'Get peers from {name} ')
    url = convert_idna_address(f"https://{name}/api/v1/instance/peers")
    # properly encode urls that have emoji characters or other unicode
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=user_agent_header, timeout=10)
            r.raise_for_status()
            return r.json()
    except json.JSONDecodeError as e:
        logging.error(f'JSON Error: {e}')
        return []
    except httpx.HTTPStatusError as e:
        logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        return []
    except httpx.RequestError as e:
        logging.error(f'Connection Error {e} on {url}')
        return []
    except InvalidCodepoint as e:
        print(f'Invalid URL: {url}')
        logging.error(f'{e} {url}')
        if IGNORE_EMOJI_URL:
            return []
        return get_peers_sync(url)
    except Exception as e:
        logging.exception(f'{name} {url} {e}')
        print(f'UNKNOWN EXCEPTION: {url} {name} {e}')
        return []


def write_data(instance, peers, i_file, g_file):
    if CREATE_GRAPH:
        data = {instance: peers}  # store graph data
        with open(g_file, 'a') as f:
            s = json.dumps(data)
            f.write(s + '\n')
    with open(i_file, 'a') as f:  # store instances
        f.write(instance.encode('unicode_escape').decode() + '\n')


async def crawl_peers(known, unknown, i_file, g_file, z_file):
    """
    get peers, if peers are not on the know list, scan to read their peers
    repeat crawling down the peers - until all are known

    i_file is output, g_file to create graph, z for zero_peers
    """
    unknowns_written = False
    while unknown:
        instance = unknown.pop()
        known.add(instance)
        if 'sleeping.town' in instance:  # debug hack
            logging.info(f'{instance} calling get_peers()')
        peers = await get_peers(instance)
        if 'sleeping.town' in instance:  # debug hack
            logging.info(f'{instance} returned {peers}')

        # filter out error or odd conditions from peers list
        if not isinstance(peers, list):
            logging.error(f'{instance} did not return a list')
            peers = []
        while None in peers:  # some sites have a trailing None in the list
            peers.remove(None)
        peers = [x for x in peers if not any([x.endswith('activitypub-troll.cf'),
                                              x.endswith('misskey-forkbomb.cf'),
                                              x.endswith('repl.co'),
                                              x.endswith('gab.best'),
                                              x.endswith('ngrok.io'),
                                              x.endswith('cispa.saarland'),
                                              x.endswith('.local'),
                                              x.startswith("192."),
                                              x in ('sleeping.town', 'mastodon.sleeping.town'),
                                              ':' in x,
                                              '..' in x,
                                              '.' not in x,
                                              len(x.split('.')[0]) >= 40,
                                              x.split('.')[0].isupper(),
                                              ])]
        if peers:  # don't save data without peers - indicates an issue
            write_data(instance, peers, i_file, g_file)
        # naughty list -- domains not to scan...don't scan domains with no peers
        else:
            with open(z_file, 'a') as f:
                f.write(instance.encode('unicode_escape').decode() + '\n')
        new_unknown_peers = set(peers) - known
        unknown.update(new_unknown_peers)
        print(f'{instance} Number of peers: {len(peers)}; Number unknown {len(unknown)}')
        if not unknowns_written and len(unknown) >= 60_000:
            # write list of unknowns, this helps to identify "junk sites"
            data = [d.encode('unicode_escape').decode() + '\n' for d in list(unknown)]
            with open('unknowns.txt', 'w') as f:
                f.writelines(data)
            unknowns_written = True


async def get_instances(ignore_zero_peers=True):
    logfile = Path('get_instances_log.txt')
    logfile.unlink(missing_ok=True)
    logging.basicConfig(filename=logfile, level=logging.ERROR)
    instances_file = Path('mastodon_instances.txt')
    instances_file.unlink(missing_ok=True)
    graph_file = Path('graph.txt')
    graph_file.unlink(missing_ok=True)
    zero_peers_file = Path('zero_peers.txt')

    with open('seed_instances.json') as f:
        seed_instances = json.load(f)

    # seed_instances = ['🍺🌯.to']  # test case for invalid url in httpx

    known = set()
    unknown = set(seed_instances)  # set of not yet scanned instances
    # if zero_peers_file exists, add them to known set.
    if not ignore_zero_peers and zero_peers_file.exists():
        print('loading zero peers file...', end='')
        with open(zero_peers_file) as f:
            zp = f.read().splitlines()
        known.update(zp)
        print('completed')
    zero_peers_file.unlink(missing_ok=True)
    unknown = unknown - known

    async with trio.open_nursery() as nursery:
        for _ in range(100):
            nursery.start_soon(crawl_peers, known, unknown, instances_file, graph_file, zero_peers_file)
    print('Done!')


if __name__ == '__main__':
    with keepawake(keep_screen_awake=False):
        trio.run(get_instances)
