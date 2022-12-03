from datetime import datetime, timezone
import json
from pathlib import Path
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

#todo: add a resume file that captures the last offset, so a file can be resumed.

class GetMastodonData:
    def __init__(self, fn='mastodon_users.txt', fail_fn='checkpoint.txt', server='mastodon.social'):
        self.data_fn = Path(fn)
        self.data_fn.unlink(missing_ok=True)
        self.fail_fn = Path(fail_fn)  # urls that do not successfully return data
        self.fail_fn.unlink(missing_ok=True)
        self.url_g = (f"https://{server}/api/v1/directory?order=new?limit=80?offset={i * 80}" for i in range(10_000))
        self.server = server
        self.last_reset_time = datetime.now(timezone.utc)
        self.fail_count = 0
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
            if rate_limit_remaining == '0':
                raise ValueError('Rate Limit Remaining is Zero')
            reset_time = datetime.fromisoformat(rate_limit_reset.replace('Z', '+00:00'))
            self.last_reset_time = max(self.last_reset_time, reset_time)
        except KeyError as e:
            print(f'{e} : {d}')

    async def get_data(self):
        async with httpx.AsyncClient() as client:
            url = next(self.url_g)
            response = await client.get(url, timeout=180)  # allow three minutes for a get() to complete
            self._set_last_reset_time(response)
            self.save(response, url)

    def number_of_users(self):
        response = httpx.get(f"https://{self.server}/api/v1/instance")
        instance = response.json()
        self._set_last_reset_time(response)
        return int(instance['stats']['user_count'])

    def save(self, r, url):
        users = r.json()
        for user in users:
            with open('all.txt', 'a') as f:
                json.dump(user, f)
                f.write('\n')
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
    gmd = GetMastodonData()
    users = gmd.number_of_users()
    print(f'User count: {users}')
    s_req = 10  # number of simultaneous requests
    while users >= s_req:
        for _ in range(30): # 30 x 10 = 300 calls
            async with trio.open_nursery() as nursery:
                start = trio.current_time()
                for _ in range(s_req):  # 10 requests at a time, works without server failures on mastodon.social
                    nursery.start_soon(gmd.get_data)
                    users -= 80  # get 80 users per call
                print("Requests have been scheduled...")
            print(f'Competed successfully! {users=} Seconds remaining to limit reset: {gmd.seconds_remaining}')
            # target 300 call/5min, 1 call/sec... add wait to slow down to that rate
            elapsed_time = trio.current_time() - start
            print(f'{elapsed_time=}')
            if elapsed_time < 10:
                await trio.sleep(10.1 - elapsed_time)
    print(f'wait complete, Number of failures: {gmd.fail_count}')


trio.run(main)
