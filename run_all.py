"""
run_all.py run all phases to collect all the mastodon user data
1) run crawl_instances.py, create mastodon_instances.txt
2) run get_intantance_info.py, create instanance_info.txt, contains the instance records for all the instances
3) run get_all_users, creates the resultes directory, with the users of each instance
"""
from datetime import datetime

import trio

import crawl_instances
import get_instance_info
import get_all_users

start = datetime.now()
trio.run(crawl_instances.main)
end = datetime.now()
crawl_time = end - start

start = datetime.now()
trio.run(get_instance_info.main)
end = datetime.now()
get_info_time = end - start

tart = datetime.now()
trio.run(get_all_users.main)
end = datetime.now()
get_users_time = end - start

print(f'Time to crawl all instances: {crawl_time}')
print(f'Time to get instance info: {get_info_time}')
print(f'Time to get all users: {get_users_time}')
print(f'Total execution time: {crawl_time + get_info_time + get_users_time}')
print('mastodon_instances.txt - List of all servers')
print('instance_info.txt - info records for all servers')
print('results directory - contains files with all users per server')