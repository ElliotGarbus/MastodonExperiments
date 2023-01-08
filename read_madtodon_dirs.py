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
    params = {'count': f'{n}', 'include_down': 'false', 'language': 'en', 'sort_by': 'users', 'sort_order': 'desc'}
    r = httpx.get('https://instances.social/api/1.0/instances/list',headers=header, params=params)
    d = r.json()
    return d['instances']  # keys of interest: 'name', 'users', 'active_users'

def save_users(users, server, active_users, all_users):
    try:
        users = users.json()
    except json.decoder.JSONDecodeError as e:
        logging.error(f'JSON error {e}')
        return
    unique_url = set()
    for user in users:  # todo: put the loop inside the file context
        # print(user)
        if user['url'] in unique_url:
            continue
        unique_url.add(user['url'])
        with open('users.txt', 'a') as f:  # only save unique data
            json.dump(user, f)
            f.write('\n')
    print(f'saved {server}')
    logging.info(f'{server} received {len(users)} records, {len(unique_url)} unique records;'
                 f'of users: {all_users}, number of active Users: {active_users}')


async def get_users(instance):
    server = instance['name']
    active_users = instance['active_users']
    users = instance['users']
    print(f'getting {server}')
    url = f"https://{server}/api/v1/directory"
    params = {'local': True, 'limit': 40 }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, params=params, timeout=180)  # allow three minutes
            r.raise_for_status()
            save_users(r, server, active_users, users)
        except httpx.HTTPStatusError as e:
            logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logging.error(f'Error {e} on {url}')


async def main():
    log_fn = Path('log.txt')
    log_fn.unlink(missing_ok=True)
    users_fn = Path('users.txt')
    users_fn.unlink(missing_ok=True)

    logging.basicConfig(filename=log_fn, encoding='utf-8', level=logging.DEBUG)
    print('getting instances')
    instances = get_instances(0)  # 0 is all instances
    start = time.perf_counter()
    print('instances received, schedule get_users')
    async with trio.open_nursery() as nursery:
        for mi in instances:
            nursery.start_soon(get_users, mi)
    print('Done!')
    t = time.perf_counter() - start
    print(f'{t} seconds for {len(instances)} servers; {t/len(instances)} sec/instance')

trio.run(main)
