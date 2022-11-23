import requests
import json
from datetime import datetime
from pprint import pprint
from pathlib import Path


response = requests.get("https://mastodon.social/api/v1/instance")
print(f"{response.headers['X-RateLimit-Remaining']=} {response.headers['X-RateLimit-Reset']=}")
instance = json.loads(response.text)
print(f"Users: {instance['stats']['user_count']}")

# pprint(instance)
# print('=' * 80)

path = Path('mastodon_users.txt')
path.unlink(missing_ok=True)

for i in range(301):
    response = requests.get(f"https://mastodon.social/api/v1/directory?limit=80?offset={i*80}")
    print(f"{response.headers['X-RateLimit-Remaining']=} {response.headers['X-RateLimit-Reset']=}")
    if response.headers['X-RateLimit-Remaining'] == '0':
        print('*' * 80)
        print(datetime.now())
    users = json.loads(response.text)
    # pprint(users)
    for user in users:
        with open(path, 'a') as f:
            json.dump(user, f)
            f.write('\n')

