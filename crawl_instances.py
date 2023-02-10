# visit all known instances, identify new peers, and scan for new instances

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
import warnings

import httpx
import trio
from tenacity import (AsyncRetrying, stop_after_attempt, TryAgain, wait_fixed, after_log,
                      retry_if_exception_type, RetryError)
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)


async def get_peers(name):
    url = f"https://{name}/api/v1/instance/peers"
    logging.info(f'URL: {url}')
    print(f'Get peers from {name} ')
    async with httpx.AsyncClient() as client:
        try:
            async for attempt in AsyncRetrying(sleep=trio.sleep, stop=stop_after_attempt(5),
                                               wait=wait_fixed(5),
                                               retry=retry_if_exception_type(
                                                   (TryAgain, httpx.ConnectError, httpx.TimeoutException))):
                with attempt:
                    r = await client.get(url, timeout=180)  # allow three minutes
                    if r.status_code == 503 or (name == 'mastodon.social' and r.status_code != 200):
                        raise TryAgain
                    r.raise_for_status()
                    return r
        except httpx.HTTPStatusError as e:
            logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        except httpx.RemoteProtocolError as e:
            logging.error(f'Connection Error {e} on {url}')
        except RetryError:
            logging.error('Finished retries with no response')
        except Exception as e:
            logging.exception(e)

async def crawl_peers(name, known):
    """
    get peers, if peers are not on the know list, scan to read their peers
    repeat crawling down the peers - until all are known
    """
    start = True
    unknown = None
    while start or unknown:
        instance = name if start else unknown.pop()
        start = False
        r = await get_peers(instance)  # could create a new nursery but of little value if most are known
        try:
            peers = r.json()
            peers = [instance for instance in peers if not peers.endswidth('activitypub-troll.cf') ]
            print(f'{peers=}')
        except (AttributeError, json.decoder.JSONDecodeError):
            continue
        unknown = set(peers) - known
        known.update(unknown)  # add the newly found instances to the known list


async def main():
    logging.basicConfig(filename='rootlog.log', level=logging.DEBUG)
    with open('mastodon_instances.txt') as f:  # todo: add exception handling
        instances = json.load(f)
    known = set(instances)

    async with trio.open_nursery() as nursery:
        for mi in instances:
            nursery.start_soon(crawl_peers, mi, known)
    print(known)
    with open('out_mastodon_instances.txt', 'w') as f:
        json.dump(list(known), f)


    print('Done!')


if __name__ == '__main__':
    # with keepawake(keep_screen_awake=False):
    trio.run(main)
