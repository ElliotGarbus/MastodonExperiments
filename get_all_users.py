import json
import logging
import warnings
from datetime import datetime
from pathlib import Path

import httpx
import trio
from tenacity import (AsyncRetrying, stop_after_attempt, TryAgain, wait_fixed, after_log,
                      retry_if_exception_type, RetryError)
from trio import TrioDeprecationWarning
from wakepy import keepawake

from mastodon_instances_key import mi_info

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

"""
format of mi_info
mi_info = {'name':'app_name',
           'app-id':'app_id number',
           'token': 'token string'}
"""


def get_instances(n):
    # returns a list of servers, uses instances.social api  https://instances.social/api/doc/
    header = {'Authorization': 'Bearer ' + mi_info['token']}
    params = {'count': n, 'include_down': True, 'language': 'en', 'sort_by': 'users', 'sort_order': 'desc'}
    r = httpx.get('https://instances.social/api/1.0/instances/list', headers=header, params=params)
    d = r.json()
    return d['instances']  # keys of interest: 'name', 'users', 'active_users'


def delete_files(p_dir):
    # p_dir is a directory Path object
    for file in p_dir.glob('*.*'):
        file.unlink()


class MastodonInstance:
    def __init__(self, name, results_dir, log_dir):
        self.name = name
        fn = self.name.replace('.', '_') + '.txt'
        self.data_fn = results_dir / fn
        log_fn = log_dir / fn
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_fn)
        formatter = logging.Formatter('{levelname}:{asctime}:{name}:{message}',
                                      style='{', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.params_g = ({'order': 'active', 'local': True, 'limit': 40, 'offset': i} for i in range(0, 100000000, 40))
        self.unique_url = set()
        self.finished = False  # used to indicate end of scan, or fatal error

    def save(self, r):
        print(f'save {self.name} {datetime.now():%m/%d/%Y %H:%M:%S}')
        try:
            users = r.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f'JSON error {e}')
            self.finished = True
            return
        with open(self.data_fn, 'a') as f:  # only save unique data
            for user in users:
                # print(user)
                if user['url'] in self.unique_url:
                    continue
                self.unique_url.add(user['url'])
                json.dump(user, f)
                f.write('\n')
        self.logger.info(f'{len(self.unique_url)} unique records')
        if not users:
            self.logger.info('All Data Returned')
            self.finished = True

    async def get_users(self):
        url = f"https://{self.name}/api/v1/directory"
        print(f'Get users from {self.name} ')
        async with httpx.AsyncClient() as client:
            while not self.finished:
                try:
                    async for attempt in AsyncRetrying(sleep=trio.sleep, stop=stop_after_attempt(5),
                                                       wait=wait_fixed(5),
                                                       retry=retry_if_exception_type(
                                                           (TryAgain, httpx.ConnectError, httpx.TimeoutException)),
                                                       after=after_log(self.logger, logging.DEBUG)):
                        with attempt:
                            start = trio.current_time()
                            r = await client.get(url, params=next(self.params_g), timeout=10)
                            if r.status_code == 503 or (self.name == 'mastodon.social' and r.status_code != 200):
                                raise TryAgain
                            r.raise_for_status()
                            elapsed_time = trio.current_time() - start
                            if elapsed_time < 1:
                                await trio.sleep(1 - elapsed_time)  # one second per call rate limit
                            self.save(r)
                except httpx.HTTPStatusError as e:
                    self.logger.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
                    self.finished = True
                except (httpx.RemoteProtocolError) as e:
                    self.logger.error(f'Connection Error {e} on {url}')
                    self.finished = True
                except RetryError:
                    self.logger.error('Finished retries with no response')
                    self.finished = True


async def main():
    # logging.basicConfig(filename='rootlog.log', level=logging.DEBUG)
    log_dir = Path('log')
    log_dir.mkdir(exist_ok=True)
    delete_files(log_dir)
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    delete_files(results_dir)
    print('getting instances')
    instances = get_instances(0)  # 0 is all instances
    print('instances received')
    mis = []
    for instance in instances:
        mis.append(MastodonInstance(instance['name'], results_dir, log_dir))

    async with trio.open_nursery() as nursery:
        for mi in mis:
            nursery.start_soon(mi.get_users)
    print('Done!')


if __name__ == '__main__':
    with keepawake(keep_screen_awake=False):
        trio.run(main)
