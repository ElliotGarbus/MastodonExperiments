from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

# todo add logging
# todo: add cli?

class GetMastodonData:
    def __init__(self, fail_fn='checkpoint.txt', server='mastodon.social'):
        self.data_fn = Path(server.replace('.', '_') + '_users.txt')
        print(self.data_fn)
        self.data_fn.unlink(missing_ok=True)
        self.fail_fn = Path(fail_fn)  # urls that do not successfully return data
        self.fail_fn.unlink(missing_ok=True)
        self.url_g = (f"https://{server}/api/v1/directory?limit=80?offset={i * 80}" for i in range(0, 100_000))
        self.server = server
        self.last_reset_time = datetime.now(timezone.utc)
        self.fail_count = 0
        self.time_outs = 0
        self.unique_url = set()

    @property
    def seconds_remaining(self):
        # only valid after at least one data access
        return (self.last_reset_time - datetime.now(timezone.utc)).total_seconds()

    def _set_last_reset_time(self, response):
        d = dict(response.headers)
        try:
            rate_limit_reset = d['x-ratelimit-reset']
            rate_limit_remaining = d['x-ratelimit-remaining']
            print(f"{rate_limit_remaining=} {rate_limit_reset=}")
            reset_time = datetime.fromisoformat(rate_limit_reset.replace('Z', '+00:00'))
            self.last_reset_time = max(self.last_reset_time, reset_time)
            if rate_limit_remaining == '0':
                print('Rate Limiting timeout reached, waiting 5 minutes for reset ')
                trio.sleep(300) # Wait for rate limiting to reset

        except KeyError as e:
            print(f'{e} : {d}')

    async def get_data(self):
        async with httpx.AsyncClient() as client:
            url = next(self.url_g)
            try:
                response = await client.get(url, timeout=180)  # allow three minutes for a get() to complete
                self._set_last_reset_time(response)
                self.save(response, url)
            except (httpx.TimeoutException, httpx.ConnectError):
                # data is sparse and repetitive - just count timeout errors
                self.time_outs += 1
                print(f'http.Timeout Exception total: {self.time_outs}')

    def number_of_users(self):
        response = httpx.get(f"https://{self.server}/api/v1/instance")
        instance = response.json()
        self._set_last_reset_time(response)
        return int(instance['stats']['user_count'])

    def save(self, r, url):
        try:
            users = r.json()
        except json.JSONDecodeError:
            print('Invalid JSON in response, Response is ignored')
            # todo:  add count of invalid responses
            return
        for user in users:
            # with open('all.txt', 'a') as f:
            #     json.dump(user, f)
            #     f.write('\n')
            if user == 'error':
                self.fail_count += 1
                # print(f'Error detected: {user}')
                with open(self.fail_fn, 'a') as ffn:
                    ffn.write(f'{url}\n')
                continue

            if user['url'] in self.unique_url:
                print(f"user not unique: {user['url']}")
                continue

            self.unique_url.add(user['url'])

            with open(self.data_fn, 'a') as f:
                json.dump(user, f)
                f.write('\n')
                print(f"{user['url']} followers: {user['followers_count']}")
            with open('last_url.txt', 'w') as f:
                f.write(url)


async def main():
    hours = 3  # run time in hours
    try:
        server = sys.argv[1]
        gmd = GetMastodonData(server=server)
    except IndexError:
        gmd = GetMastodonData()
    users = 700_000 # gmd.number_of_users() # number of call sets for just under 3 hours.
    print(f'User count: {users}')
    s_req = 10  # number of simultaneous requests
    with trio.move_on_after(60 * 60 * hours) as cancel_scope:
        while True:
            for _ in range(30): # 30 x 10 = 300 calls
                async with trio.open_nursery() as nursery:
                    start = trio.current_time()
                    for _ in range(s_req):  # 10 requests at a time, works without server failures on mastodon.social
                        nursery.start_soon(gmd.get_data)
                        # users -= 80  # get 80 users per call -- due to pagination bug no connection to user count
                    print(f'{s_req} Requests have been scheduled...')
                print(f'Competed successfully! Seconds remaining to limit reset: {gmd.seconds_remaining}')
                # target 300 call/5min, 1 call/sec... add wait to slow down to that rate
                elapsed_time = trio.current_time() - start
                print(f'{elapsed_time=}')
                if elapsed_time <= 10:
                    await trio.sleep(12 - elapsed_time)  # add some buffer to the time
                print(f'wait complete, Number of invalid user records: {gmd.fail_count}, Number of Network timeouts {gmd.time_outs}')
            if cancel_scope.cancelled_caught:
                print('Execution Completed Normally, scheduled execution time has expired')
                print(f'Number of invalid user records: {gmd.fail_count}, Number of Network timeouts {gmd.time_outs}')
            else:
                print('Exit with unhandled exception')


trio.run(main)
