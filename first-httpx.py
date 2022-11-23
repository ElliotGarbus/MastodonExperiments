import trio
import httpx
import warnings
from trio import TrioDeprecationWarning
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

url_g = (f"https://mastodon.social/api/v1/directory?limit=80?offset={i * 80}" for i in range(100))


async def get_header():
    async with httpx.AsyncClient() as client:
        response = await client.get(next(url_g), timeout=60)
        d = dict(response.headers)
        print(f"{d['x-ratelimit-remaining']=} {d['x-ratelimit-reset']=}")



async def main():
    with trio.move_on_after(300) as cancel_scope:
        async with trio.open_nursery() as nursery:
            for _ in range(50):
                nursery.start_soon(get_header)
            print("waiting for children to finish...")
            # -- we exit the nursery block here --
    print(f'{cancel_scope.cancelled_caught=}')
    print("parent: all done!")


trio.run(main)
