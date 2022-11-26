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
    url_g = None
    last_reset_time = datetime.now(timezone.utc)

    def __init__(self, fn='mastodon_users.txt', chkpt_fn='checkpoint.txt', server='mastodon.social'):
        self.data_path = Path(fn)
        self.data_path.unlink(missing_ok=True)
        self.url_g = (f"https://{server}/api/v1/directory?limit=80?offset={i * 80}" for i in range(500))

    async def get_data(self):
        async with httpx.AsyncClient() as client:
            url = next(self.url_g)
            response = await client.get(next(self.url_g), timeout=180)  # allow three minutes for a get() to complete
            d = dict(response.headers)
            try:
                rate_limit_reset = d['x-ratelimit-reset']
                rate_limit_remaining = d['x-ratelimit-remaining']
                print(f"{rate_limit_remaining=} {rate_limit_reset=}")
                if rate_limit_remaining == '0':
                    raise ValueError('Rate Limit Remaining is Zero')
                reset_time = datetime.fromisoformat(d['x-ratelimit-reset'].replace('Z', '+00:00'))
                self.last_reset_time = max(self.last_reset_time, reset_time)
            except KeyError as e:
                print(f'{e} : {d}')
            self.save(response, url)

    def save(self, r, url):
        users = r.json()
        for user in users:
            with open(self.data_path, 'a') as f:
                json.dump(user, f)
                f.write('\n')
            try:
                print(f"{user['url']} followers: {user['followers_count']}")
            except (KeyError, TypeError):
                print(f'Error: {user} {url}')


async def main():
    gmd = GetMastodonData()
    with trio.move_on_after(5 * 60) as cancel_scope:  # cancel after 5 min
        async with trio.open_nursery() as nursery:
            for _ in range(50):
                nursery.start_soon(gmd.get_data)
            print("Requests have been scheduled...")
    if cancel_scope.cancelled_caught:
        print('ERROR: time limit exceeded')
    else:
        print('Competed successfully!')
    print(f'last_reset_time:\t{gmd.last_reset_time:%H:%M:%S}')
    print(f'now:\t\t\t\t{datetime.now(timezone.utc):%H:%M:%S}')
    sleep_time = (gmd.last_reset_time - datetime.now(timezone.utc)).total_seconds()
    print(f'sleeping... wait time (sec): {sleep_time}')
    if sleep_time > 0:
        await trio.sleep(sleep_time)
    else:
        print('Negative Sleep time??!?!')
    print('wait complete')

trio.run(main)
