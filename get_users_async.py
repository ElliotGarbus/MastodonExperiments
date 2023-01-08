import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)


class GetMastodonData:
    def __init__(self,  server='mastodon.social', local='true'):
        # local is part of the url, users local to the server 'true' or 'false'
        save_dir = Path('results')
        save_dir.mkdir(exist_ok=True)
        dt = datetime.now().isoformat(timespec='seconds').replace(':', '_')  # part of fine name
        fn = server.replace('.', '_') + '_' + dt + '.txt'
        self.data_fn = save_dir / fn
        print(f'Data will be saved to: {self.data_fn}')
        log_dir = Path('log')
        log_dir.mkdir(exist_ok=True)
        log_fn = log_dir / fn
        logging.basicConfig(filename=log_fn, encoding='utf-8', level=logging.DEBUG)
        self.url_g = (f"https://{server}/api/v1/directory?local={local}?limit=80?offset={i * 80}" \
                      for i in range(0, 100_000))
        self.server = server
        self.last_reset_time = datetime.now(timezone.utc)
        self.unique_url = set()
        self._stats = {'json errors': 0, 'network errors': 0, 'bad headers': 0, 'invalid user record': 0,
                       'total records': 0}

    @property
    def seconds_remaining(self):
        # only valid after at least one data access
        return (self.last_reset_time - datetime.now(timezone.utc)).total_seconds()

    @property
    def stats(self):
        summary = ''
        for k, v in self._stats.items():
            summary += f'{k} = {v}; '
        summary += f'Unique urls: {len(self.unique_url)}'
        return summary

    async def _set_last_reset_time(self, response):
        d = dict(response.headers)
        try:
            rate_limit_reset = d['x-ratelimit-reset']  # time until the rate limit resets
            rate_limit_remaining = d['x-ratelimit-remaining']  # number of messages allowed until reset
            print(f"{rate_limit_remaining=} {rate_limit_reset=}")
            reset_time = datetime.fromisoformat(rate_limit_reset.replace('Z', '+00:00'))
            self.last_reset_time = max(self.last_reset_time, reset_time)
            if rate_limit_remaining == '0':
                print('Rate Limiting timeout reached, waiting for reset ')
                logging.info('Rate limit reached')
                await trio.sleep(30) # Wait for rate limiting to reset, Should be enough for the count to roll-over

        except KeyError as e:
            self._stats['bad headers'] += 1
            print(f'{e} : {d}')


    async def get_data(self):
        async with httpx.AsyncClient() as client:
            url = next(self.url_g)
            try:
                r = await client.get(url, timeout=180)  # allow three minutes for a get() to complete
                r.raise_for_status()
                await self._set_last_reset_time(r)
                self.save(r, url)
            except httpx.HTTPStatusError as e:
                logging.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
                sys.exit(0)
            except (httpx.TimeoutException, httpx.ConnectError):
                # data is sparse and repetitive - just count timeout errors
                self._stats['network errors'] += 1
                print(f'Network Exception, total: {self._stats["network errors"]}')


    async def number_of_users(self):
        # not currently being called
        response = httpx.get(f"https://{self.server}/api/v1/instance", timeout=180)  # extended timeout to reduce errors
        instance = response.json()
        await self._set_last_reset_time(response)
        return int(instance['stats']['user_count'])

    def save(self, r, url):
        try:
            users = r.json()
        except json.JSONDecodeError:
            print('Invalid JSON in response, Response is ignored')
            self._stats['json errors'] += 1
            return
        for user in users:
            self._stats['total records'] += 1
            # with open('all.txt', 'a') as f:  # save all data, for debug
            #     json.dump(user, f)
            #     f.write('\n')
            if user == 'error':
                self._stats['invalid user record'] += 1
                # print(f'Error detected: {user}')
                # this was here to capture failed requests to replay them, given the issues with the api,
                # and the redudant data - this is commented out
                # with open(self.fail_fn, 'a') as ffn:
                #     ffn.write(f'{url}\n')
                continue
            if user['url'] in self.unique_url:
                print(f"user not unique: {user['url']}")
                continue

            self.unique_url.add(user['url'])

            with open(self.data_fn, 'a') as f:  # only save unique data
                json.dump(user, f)
                f.write('\n')
                print(f"{user['url']} followers: {user['followers_count']}")
            # used to capture the last url - used to resume a search (not used)
            # with open('last_url.txt', 'w') as f:
            #     f.write(url)


async def main(server, min):
    gmd = GetMastodonData(server=server)
    # print(f'User count: {gmd.number_of_users()}')  # unused, was for looping over user count
    s_req = 10  # number of simultaneous requests
    with trio.move_on_after(60 * min) as cancel_scope:
        while not cancel_scope.cancelled_caught:
            for _ in range(30): # 30 x 10 = 300 calls
                async with trio.open_nursery() as nursery:
                    start = trio.current_time()
                    for _ in range(s_req):  # 10 requests at a time, works without server failures on mastodon.social
                        nursery.start_soon(gmd.get_data)
                    print(f'{s_req} Requests have been scheduled...')
                print(f'Competed successfully! Seconds remaining to limit reset: {gmd.seconds_remaining}')
                # target 300 call/5min, 1 call/sec... add wait to slow down to that rate
                elapsed_time = trio.current_time() - start
                print(f'{elapsed_time=}')
                if elapsed_time <= 10:
                    await trio.sleep(12 - elapsed_time)  # add some buffer to the time
                print(f'wait complete, {gmd.stats}')
    if cancel_scope.cancelled_caught:
        print('Execution Completed Normally, scheduled execution time has expired')
        print(gmd.stats)
        logging.info(gmd.stats)

if __name__ == '__main__':
    description = 'Uses the Mastodon Directory API, to save users to a file. ' \
                  'The file name contains the server name and date & time. '\
                  'Each line is a dictionary of user data (JSON).'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('server', help='Name of the server to search, example: "mastodon.social"')
    parser.add_argument('-t', '--time', default=5,  help="execution time in minutes, defaults to 5 minutes", type=float)
    args = parser.parse_args()

    trio.run(main, args.server, args.time)
