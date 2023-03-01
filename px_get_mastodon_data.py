"""
px_get_mastodon_data.py run all phases to collect all the mastodon user data
1) run p1_get_instances.py, create mastodon_instances.txt
2) run p2_get_instance_info.py, create instance_info.txt, contains the instance records for all the instances
3) run p3_get__users, creates the "results" directory, with the users of each instance
"""
from datetime import datetime, timedelta
import argparse

import trio
from wakepy import keepawake

from p1_get_instances import get_instances
from p2_get_instance_info import get_instance_info
from p3_get_users import get_users

description = 'Get the mastodon instance info and optionally user data.'
mode_help = '"info" collects the instance info for all servers, "users" collects the info and user data. '\
            'Defaults to "users"'
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-m', '--mode', default='users', help=mode_help, choices=['info', 'users'])
args = parser.parse_args()


phases = ({'function': get_instances, 'timer_key': 'get_instances_time'},
          {'function': get_instance_info, 'timer_key': 'get_info_time'},
          {'function': get_users, 'timer_key': 'get_users_time'})
timer = {}

if args.mode == 'info':
    phases = phases[:2]

with keepawake(keep_screen_awake=False):
    for phase in phases:
        start = datetime.now()
        trio.run(phase['function'])
        end = datetime.now()
        timer[phase['timer_key']] = end - start

total_time = sum(timer.values(), start=timedelta())
# convert to str, drop microseconds
total_time = str(total_time).split('.')[0]
for k in timer:
    timer[k] = str(timer[k]).split('.')[0]

print('=' * 80)
print(f'Time to get instances: {timer["get_instances_time"]}')
print(f'Time to get instance info: {timer["get_info_time"]}')
try:
    print(f'Time to get all users: {timer["get_users_time"]}')
except KeyError:
    pass
print(f'Total execution time: {total_time}')
print('mastodon_instances.txt - List of all servers')
print('instance_info.txt - info records for all servers')
print('results directory - contains files with all users per server')
print('=' * 80)
