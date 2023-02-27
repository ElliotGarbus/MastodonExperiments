"""
run_all.py run all phases to collect all the mastodon user data
1) run crawl_instances.py, create mastodon_instances.txt
2) run get_instance_info.py, create instance_info.txt, contains the instance records for all the instances
3) run get_all_users, creates the "results" directory, with the users of each instance
"""
from datetime import datetime, timedelta

import trio
from wakepy import keepawake

import crawl_instances
import get_instance_info
import get_all_users

with keepawake(keep_screen_awake=False):
    phases = ({'function': crawl_instances.main, 'timer_key': 'crawl_time'},
              {'function': get_instance_info.main, 'timer_key': 'get_info_time'},
              {'function': get_all_users.main, 'timer_key': 'get_users_time'})
    timer = {}

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
    print(f'Time to crawl all instances: {timer["crawl_time"]}')
    print(f'Time to get instance info: {timer["get_info_time"]}')
    print(f'Time to get all users: {timer["get_users_time"]}')
    print(f'Total execution time: {total_time}')
    print('mastodon_instances.txt - List of all servers')
    print('instance_info.txt - info records for all servers')
    print('results directory - contains files with all users per server')
    print('=' * 80)
