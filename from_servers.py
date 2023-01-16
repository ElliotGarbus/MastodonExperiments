# from_servers.py - kick of  a number of processes to pull data from multiple servers
# todo add ui?
import argparse
from itertools import islice
from subprocess import DEVNULL

import trio

from get_instances import get_instances


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


async def launch_process(server, minutes):
    print(f'Scheduling directory scan of {server} for {minutes} minutes')
    await trio.run_process(['python', '.\get_users_async_forward.py', server, '-t', f'{minutes}'],
                           shell=True, stdout=DEVNULL)
    print(f'{server} scan complete')


async def main(duration):
    broken_servers = ['loforo.com', 'mas.town', 'mastodon.top', 'meow.social']
    servers = get_instances(300)  # 0 for all servers
    print(f'{len(servers)} servers selected')
    for s in broken_servers:
        servers.remove(s)
    for batch in batched(servers, 25):  # process 25 at a time - this can be adjusted for platform
        async with trio.open_nursery() as nursery:
            for s in batch:
                nursery.start_soon(launch_process, s, duration)
    print('All Done!')


if __name__ == '__main__':
    description = 'Access multiple servers to access their directory data ' \
                  'get_users_async.py is used to collect the data ' \
                  'resulting data files are stored in the results directory'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-t', '--time', default=5, help="execution time in minutes, defaults to 5 minutes", type=float)
    args = parser.parse_args()
    trio.run(main, args.time)
