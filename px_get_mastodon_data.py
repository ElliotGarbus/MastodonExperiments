"""
px_get_mastodon_data.py run all phases to collect all the mastodon user data
1) run p1_get_instances.py, create mastodon_instances.txt
2) run p2_get_instance_info.py, create instance_info.txt, contains the instance records for all the instances
3) run p3_get__users, creates the "results" directory, with the users of each instance
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import trio
from wakepy import keepawake

from p1_get_instances import get_instances
from p2_get_instance_info import get_instance_info
from p3_get_users import get_users


def cli():
    description = 'Get the mastodon instance info and optionally user data.'
    mode_help = '"info" collects the instance info for all servers, "users" collects the info and user data. ' \
                'Defaults to "users"'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-m', '--mode', default='users', help=mode_help, choices=['info', 'users'])
    args = parser.parse_args()
    return args.mode


def print_execution_times(t):
    # t is a dict that holds the execution times per phase
    total_time = sum(t.values(), start=timedelta())
    # convert to str, drop microseconds
    total_time = str(total_time).split('.')[0]
    for k in t:
        t[k] = str(t[k]).split('.')[0]
    print('=' * 80)
    print(f'Time to get instances: {t["get_instances_time"]}')
    print(f'Time to get instance info: {t["get_info_time"]}')
    try:
        print(f'Time to get all users: {t["get_users_time"]}')
    except KeyError:
        pass
    print(f'Total execution time: {total_time}')
    print('mastodon_instances.txt - List of all servers')
    print('instance_info.txt - info records for all servers')
    print('results directory - contains files with all users per server')
    print('=' * 80)


def consolidate_results(m):
    # m is the execution mode either 'info' or 'users' from the cli
    files = Path('results').glob('*.*')
    with open('consolidated_output.txt', 'w') as outfile:
        with open('instance_info.txt') as info_file:
            outfile.write(info_file.read())
        if m == 'users':
            for file in files:
                with open(file) as f:
                    outfile.write(f.read())


phases = ({'function': get_instances, 'timer_key': 'get_instances_time'},
          {'function': get_instance_info, 'timer_key': 'get_info_time'},
          {'function': get_users, 'timer_key': 'get_users_time'})
timer = {}

mode = cli()
if mode == 'info':
    phases = phases[:2]

with keepawake(keep_screen_awake=False):
    for phase in phases:
        start = datetime.now()
        trio.run(phase['function'])
        end = datetime.now()
        timer[phase['timer_key']] = end - start

print_execution_times(timer)
print('Consolidating results...', end='')
consolidate_results(mode)
print('Done!')