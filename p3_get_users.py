"""
if the instance_info.txt file is available, read the file, and get the instances
if the instance_info.txt file is not available use https://instances.social/ to get the instances
for each instance, use the directory api to get the user records
store the results in the "results" directory, the file names are derived from the name of the server instance
"""

import json
import logging
import time
import warnings
from datetime import datetime
from pathlib import Path
import sys

import httpx
import trio
from tenacity import (AsyncRetrying, stop_after_attempt, TryAgain, wait_fixed, after_log,
                      retry_if_exception_type, RetryError)
from trio import TrioDeprecationWarning
from wakepy import keepawake
from idna.core import InvalidCodepoint

from mastodon_instances_key import mi_info
from p2_get_instance_info import INSTANCE_API_VERSION, user_agent_header

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
    is_headers = {'Authorization': 'Bearer ' + mi_info['token']} | user_agent_header
    params = {'count': n, 'include_down': True, 'language': 'en', 'sort_by': 'users', 'sort_order': 'desc'}
    r = httpx.get('https://instances.social/api/1.0/instances/list', headers=is_headers, params=params)
    d = r.json()
    return d['instances']  # keys of interest: 'name', 'users', 'active_users'


def delete_files(p_dir):
    # p_dir is a directory Path object
    for file in p_dir.glob('*.*'):
        file.unlink()


class MastodonInstance:
    run_id = None  # hold an int from time.time_ns() used to indicate all records from the same run

    def __init__(self, name, results_dir, log_dir):
        self.name = name
        fn = self.name.replace('.', '_').replace('/', '_') + '.txt'
        self.data_fn = results_dir / fn
        log_fn = log_dir / fn
        self.logger = logging.getLogger(log_fn.stem) # sets name attribute in log output
        self.logger.setLevel(logging.INFO)
        self.file_handler = logging.FileHandler(log_fn)
        formatter = logging.Formatter('{levelname} | {asctime} | {name} | {message}', style='{')
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

        self.params_g = ({'order': 'active', 'local': True, 'limit': 40, 'offset': i} for i in range(0, 100000000, 40))
        self.unique_url = set()
        self.finished = False  # used to indicate end of scan, or fatal error

    def no_new_users(self, users):
        for user in users:
            try:
                if user['url'] not in self.unique_url:
                    return False
            except TypeError as e:
                self.logger.error(f'TypeError, not a user record: {e} {type(user)=} {user}')  # not a user record
                return True
        return True

    def save(self, r):
        print(f'save {self.name} {datetime.now():%m/%d/%Y %H:%M:%S}')
        try:
            users = r.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f'JSON error {e}')
            self.finished = True
            return
        if self.no_new_users(users):
            self.logger.info(f'{len(self.unique_url)} unique records - Ending Data Collection')
            self.finished = True
            return
        with open(self.data_fn, 'a') as f:  # only save unique data
            for user in users:
                if user['url'] in self.unique_url:  # note: invalid records captured in self.no_new_user()
                    continue
                self.unique_url.add(user['url'])
                user.update({"_data_type": "user", "_domain": self.name,
                             "_full_user": f"@{user['username']}@{self.name}",
                             "_run_id": self.run_id})
                json.dump(user, f)
                f.write('\n')
        self.logger.info(f'{len(self.unique_url)} unique records')
        # if not users:
        #     self.logger.info('All Data Returned')
        #     self.finished = True

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
                            r = await client.get(url, headers=user_agent_header, params=next(self.params_g), timeout=10)
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
                except httpx.RequestError as e:
                    self.logger.error(f'Request Error {e} on {url}')
                    self.finished = True
                except RetryError:
                    self.logger.error('Finished retries with no response')
                    self.finished = True
                except InvalidCodepoint:
                    self.logger.error('Invalid codepoint, emoji {url}')
                    # Ignore urls with emoji. get_users to work with emojis not implemented
                    self.finished = True
        self.file_handler.close()


async def worker(instances, results_dir, log_dir, user_excludes):
    while instances:
        instance = instances.pop()
        if instance not in user_excludes:  # bad instances go here
            mi = MastodonInstance(name=instance, log_dir=log_dir, results_dir=results_dir)
            await mi.get_users()


def read_instance_file(file):
    """
    read the file, convert to json, sort based on api version, remove sites with zero users
    return list of instances sorted largest users to the smallest
    :param file: file handle
    :return: list of sorted instances, largest to the smallest by number of users.
    """
    data = [json.loads(x) for x in file.read().splitlines()]
    if INSTANCE_API_VERSION == 'v1':  # [stats][user_count]
        # remove instances with no users, create tuple of uri and user count
        instances = [(x['uri'],  x['stats']['user_count']) for x in data if x['stats']['user_count'] > 0]
        instances = list(set(instances))  # remove duplicates
        instances.sort(key=lambda x: x[1]) # sort based on number of users
        return [u[0] for u in instances]

    elif INSTANCE_API_VERSION == 'v2':
        raise NotImplementedError('Need to use set to remove duplicates, code not tested')
        instances = [x for x in data if x['usage']['users']['active_month'] > 0]
        instances.sort(key=lambda x: x['usage']['users']['active_month'])
        return [u['domain'] for u in instances]
    else:
        raise ValueError(f'Invalid value {INSTANCE_API_VERSION} for INSTANCE_API_VERSION')


async def get_users():
    log_dir = Path('log')
    log_dir.mkdir(exist_ok=True)
    delete_files(log_dir)
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    delete_files(results_dir)

    instance_file = Path('instance_info.txt')
    if instance_file.exists():
        with open(instance_file) as f:
            instances = read_instance_file(f)
        print(f'{len(instances)} instances read from file')
    else:
        instances = [instance['name'] for instance in get_instances(0)]  # 0 is all instances
        print('instances received from instances.social')

    exclude_file = Path('user_exclude.txt') # file holds list of instances to exclude from scan
    try:
        with open(exclude_file) as f:
            user_excludes = f.read().splitlines()
    except FileNotFoundError:
        user_excludes = []

    MastodonInstance.run_id = time.time_ns()  # set the run_id class variable
    async with trio.open_nursery() as nursery:
        for _ in range(500):  # number of concurrent tasks
            nursery.start_soon(worker, instances, results_dir, log_dir, user_excludes)
    print('Done!')


if __name__ == '__main__':
    if sys.platform == 'linux':
        trio.run(get_users)
    else:
        with keepawake(keep_screen_awake=False):
            trio.run(get_users)
