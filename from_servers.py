# from_servers.py - kick of  a number of processes to pull data from multiple servers
# todo add ui?

import argparse
import trio
from subprocess import DEVNULL

from get_instances import get_instances

servers = get_instances(100)
# servers.remove('loforo.com')  # this server throws lots of erros...
print(servers)

async def launch_process(server, hours):
    await trio.run_process(['python', '.\get_users_async.py', server, '-t', f'{hours}'],
                           shell=True, stdout=DEVNULL)

async def main(duration):
    async with trio.open_nursery() as nursery:
        for s in servers:
            print(f'Scheduling directory scan of {s} for {duration} hours')
            nursery.start_soon(launch_process, s, duration)
    print('All Done!')

if __name__ == '__main__':
    description = 'Access multiple servers to access their directory data ' \
                  'get_users_async.py is used to collect the data '\
                  'resulting data files are stored in the results directory'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-t', '--time', default=3,  help="execution time in hours, defaults to 3 hours", type=float)
    args = parser.parse_args()
    trio.run(main, args.time)

