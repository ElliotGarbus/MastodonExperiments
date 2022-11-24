from datetime import datetime, timezone
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)


class GetMastodonData:
    url_g = (f"https://mastodon.social/api/v1/directory?limit=80?offset={i * 80}" for i in range(500))
    last_reset_time = datetime.now(timezone.utc)

    async def get_header(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(next(self.url_g), timeout=180)  # allow three minutes for a get() to complete
            d = dict(response.headers)
            try:
                print(f"{d['x-ratelimit-remaining']=} {d['x-ratelimit-reset']=}")
                reset_time = datetime.fromisoformat(d['x-ratelimit-reset'].replace('Z', '+00:00'))
                self.last_reset_time = max(self.last_reset_time, reset_time)
            except (KeyError) as e:
                print(f'{e} : {d}')
            for r in response.json():
                print(r['url'])


async def main():
    gmd = GetMastodonData()
    with trio.move_on_after(300) as cancel_scope:  # cancel after 5 min
        async with trio.open_nursery() as nursery:
            for _ in range(2):
                nursery.start_soon(gmd.get_header)
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
