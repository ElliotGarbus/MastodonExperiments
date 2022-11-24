from datetime import datetime, timezone
import warnings

import httpx
import trio
from trio import TrioDeprecationWarning

# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

url_g = (f"https://mastodon.social/api/v1/directory?limit=80?offset={i * 80}" for i in range(100))


class GetMastodonData:
    last_reset_time = datetime.now(timezone.utc)

    async def get_header(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(next(url_g), timeout=120)  # allow two minutes for a get() to complete
            d = dict(response.headers)
            print(f"{d['x-ratelimit-remaining']=} {d['x-ratelimit-reset']=}")
            reset_time = datetime.fromisoformat(d['x-ratelimit-reset'])
            self.last_reset_time = max(self.last_reset_time, reset_time)
            # print(self.last_reset_time)


async def main():
    gmd = GetMastodonData()
    with trio.move_on_after(300) as cancel_scope:  # cancel after 5 min
        async with trio.open_nursery() as nursery:
            for _ in range(50):
                nursery.start_soon(gmd.get_header)
            print("waiting for children to finish...")
            # -- we exit the nursery block here --
    if cancel_scope.cancelled_caught:
        print('ERROR: time limit exceeded')
    else:
        print('Competed successfully!')
    print(f'{gmd.last_reset_time=}')


trio.run(main)
