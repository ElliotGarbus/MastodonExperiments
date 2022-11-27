import requests
import json
from pathlib import Path


response = requests.get("https://mastodon.social/api/v1/instance")
print(f"{response.headers['X-RateLimit-Remaining']=} {response.headers['X-RateLimit-Reset']=}")
instance = json.loads(response.text)
print(f"Users: {instance['stats']['user_count']}")

path = Path('mastodon_users.txt')
path.unlink(missing_ok=True)

for i in range(20):
    response = requests.get(f"https://mastodon.social/api/v1/directory?order=new?local=true?limit=40?offset={i * 40}")
    print(f"{response.headers['X-RateLimit-Remaining']=} {response.headers['X-RateLimit-Reset']=}")
    if response.status_code != 200:
        print(f'Invalid Response {response}')
    else:
        users = json.loads(response.text)
        for user in users:
            with open(path, 'a') as f:
                json.dump(user, f)
                f.write('\n')

