from datetime import datetime, timezone
import json
from pathlib import Path
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)


class GetMastodonData:
    def __init__(self, fn='mastodon_users.txt', fail_fn='checkpoint.txt', server='mastodon.social'):
        self.data_fn = Path(fn)
        self.data_fn.unlink(missing_ok=True)
        self.fail_fn = Path(fail_fn)  # urls that do not successfully return data
        self.fail_fn.unlink(missing_ok=True)
        self.url_g = (f"https://{server}/api/v1/directory?limit=80?local=true?offset={i * 80}?order=new" for i in range(10_000))
        self.server = server
        self.last_reset_time = datetime.now(timezone.utc)
        self.fail_count = 0

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
            print(f'{url=}')
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
            with open(self.data_fn, 'a') as f:
                json.dump(user, f)
                f.write('\n')
            try:
                print(f"{user['url']} followers: {user['followers_count']}")
            except (KeyError, TypeError):
                print(f'Error: {user} {url}')
                self.fail_count += 1
                with open(self.fail_fn, 'a') as ffn:
                    ffn.write(f'{url}\n')


async def main():
    gmd = GetMastodonData()
    users = gmd.number_of_users()
    print(f'User count: {users}')
    s_req = 5  # number of simultaneous requests
    # while gmd.seconds_remaining >= (60 * 5) // (300//s_req) and users >= s_req:
    while users >= s_req:
        # s_req/300 % of allowed number of messages, 5min/(300/s_req) is the time for s_req messages
        async with trio.open_nursery() as nursery:
            for _ in range(s_req):  # requests at a time that works without server failures on mastodon.social
                nursery.start_soon(gmd.get_data)
                users -= 80  # get 80 users per call
            print("Requests have been scheduled...")
        print(f'Competed successfully! {users=} {gmd.seconds_remaining=}')
    print(f'{gmd.seconds_remaining=}')
    # sleep_time = (gmd.last_reset_time - datetime.now(timezone.utc)).total_seconds()
    # print(f'sleeping... wait time (sec): {sleep_time}')
    # if sleep_time > 0:
    #     await trio.sleep(sleep_time)
    print(f'wait complete, Number of failures: {gmd.fail_count}')


trio.run(main)
