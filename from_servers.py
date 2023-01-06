# from_servers.py - kick of  a number of processes to pull data from multiple servers

import trio
from subprocess import DEVNULL

servers = ['mastodon.social', 'mas.to', 'mastodon.lol' ,'fosstodon.org']

async def launch_process(server, hours):
    await trio.run_process(['python', '.\get_users_async.py', server, '-t', f'{hours}'],
                           shell=True, stdout=DEVNULL)

async def main():
    async with trio.open_nursery() as nursery:
        for s in servers:
            print(f'launch {s}')
            nursery.start_soon(launch_process, s, .01)

if __name__ == '__main__':
    trio.run(main)

