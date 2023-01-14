from pathlib import Path
import json
import time
import logging
import warnings

import trio
from trio import TrioDeprecationWarning
import httpx
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
    header = {'Authorization': 'Bearer ' + mi_info['token'] }
    params = {'count': n, 'include_down': 'false', 'language': 'en', 'sort_by': 'users', 'sort_order': 'desc'}
    r = httpx.get('https://instances.social/api/1.0/instances/list',headers=header, params=params)
    d = r.json()
    return d['instances']  # keys of interest: 'name', 'users', 'active_users'


class MastodonInstance:
    def __init__(self, name, all_users):
        self.all_users = int(all_users)
        self.name = name
        fn = self.name.replace('.', '_') + '.txt'
        save_dir = Path('results')
        save_dir.mkdir(exist_ok=True)
        self.data_fn = save_dir / fn
        self.unique_url = set()

    @property
    def wait_time(self):  # wait time in seconds
        if self.all_users > 900_000:
            return 2 * 60  # 2 min
        elif self.all_users > 140_000:
            return 10 * 60
        elif self.all_users > 48_000:
            return 16 * 60
        else:                       # to do... add more categories...
            return 60 * 60

    def save(self, users):
        try:
            users = users.json()
        except json.decoder.JSONDecodeError as e:
            logging.error(f'JSON error {e} \n {users.text}')
            return
        with open(self.data_fn, 'a') as f:  # only save unique data
            for user in users:
                # print(user)
                if user['url'] in self.unique_url:
                    continue
                self.unique_url.add(user['url'])
                json.dump(user, f)
                f.write('\n')
        print(f'saved {self.name}')
        logging.info(f'{self.name}, total {len(self.unique_url)} unique records; '
                     f'Total users: {self.all_users}')

    async def get_users(self):
        url = f"https://{self.name}/api/v1/directory"
        params = {'local': True, 'limit': 40 }
        async with httpx.AsyncClient() as client:
            while True:                                 # todo add a time limit here...
                print(f'getting {self.name}')
                try:
                    r = await client.get(url, params=params, timeout=180)  # allow three minutes
                    r.raise_for_status()
                    self.save(r)
                except httpx.HTTPStatusError as e:
                    logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
                except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                    logging.error(f'Error {e} on {url}')
                await trio.sleep(self.wait_time)


async def main():
    log_dir = Path('log')
    log_dir.mkdir(exist_ok=True)
    log_fn = log_dir / 'log.txt'
    log_fn.unlink(missing_ok=True)
    logging.basicConfig(filename=log_fn, encoding='utf-8', level=logging.INFO)
    print('getting instances')
    instances = get_instances(10)  # 0 is all instances
    start = time.perf_counter()
    print('instances received, schedule get_users')
    mis = []
    for instance in instances:
        mis.append(MastodonInstance(instance['name'], instance['users']))

    async with trio.open_nursery() as nursery:
        for mi in mis:
            nursery.start_soon(mi.get_users)
    print('Done!')
    t = time.perf_counter() - start
    print(f'{t:0.1f} seconds for {len(instances)} servers; {t/len(instances):0.3f} sec/instance')

trio.run(main)
