import logging
import httpx
import trio
from trio import TrioDeprecationWarning
from pathlib import Path
import warnings

from tenacity import (AsyncRetrying, stop_after_attempt, TryAgain, wait_fixed, after_log,
                      RetryError, retry_if_exception_type)
# turn off deprecation warning issue with a httpx dependency, anyio
warnings.filterwarnings(action='ignore', category=TrioDeprecationWarning)

def wtf(value):
    print('wtf')
    print(value)
    return None

class MastodonInstance:
    def __init__(self, name, log_dir):
        log_fn = log_dir / 'retry.log'
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_fn)
        formatter = logging.Formatter('{levelname}:{asctime}:{name}:{message}',
                                      style='{', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    async def get_users(self):
        url = "https://httpstat.us/503"
        async with httpx.AsyncClient() as client:
            try:
                async for attempt in AsyncRetrying(sleep=trio.sleep, stop=stop_after_attempt(3),
                                                   wait=wait_fixed(.5),
                                                   retry=retry_if_exception_type((TryAgain, httpx.ConnectTimeout)),
                                                   after=after_log(self.logger, logging.DEBUG)):
                    with attempt:
                        r = await client.get(url)
                        if r.status_code == 503:
                            raise TryAgain
                        r.raise_for_status()
                        print(r)
                        # return r
            except httpx.HTTPStatusError as e:
                self.logger.error(f'Response {e.response.status_code} while requesting {e.request.url!r}.')
                print(f'Error {e.response.status_code}')
            except RetryError:
                self.logger.error('Finished retries')
                print('finished retries')

async def main():
    log_dir = Path('retry_log')
    log_dir.mkdir(exist_ok=True)
    mi = MastodonInstance('try_retry', log_dir)
    async with trio.open_nursery() as nursery:
            nursery.start_soon(mi.get_users)
    print('Done!')


trio.run(main)
