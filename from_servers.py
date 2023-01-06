# from_servers.py - kick of  a number of processes to pull data from multiple servers
import argparse
import trio
from subprocess import DEVNULL

servers = ['mastodon.social', 'mas.to', 'mastodon.lol' ,'fosstodon.org']

async def launch_process(server, hours):
    await trio.run_process(['python', '.\get_users_async.py', server, '-t', f'{hours}'],
                           shell=True, stdout=DEVNULL)

async def main(duration):
    async with trio.open_nursery() as nursery:
        for s in servers:
            print(f'Directory scan {s} for {duration} hours')
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

