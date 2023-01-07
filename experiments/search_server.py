# send search queries to a Mastodon Server
from pathlib import Path
from pprint import pp

from mastodon import Mastodon  # https://mastodonpy.readthedocs.io/en/stable/index.html

from password import user
"""
password.py holds the users password and email in the following format:
user = {'email': 'user_email_adr@email_server',
        'password': 'users mastodon password'}

"""

secrets = Path('az_social_secrets.secret')
if not secrets.exists():
    # creates public key for authentication
    Mastodon.create_app("edg_search",
                        api_base_url='https://az.social/',
                        to_file=secrets)
mastodon = Mastodon(client_id=secrets)
mastodon.log_in(username=user['email'], password=user['password'])

instance = mastodon.instance()
print(f'{instance=}')
results = mastodon.search('Austin')
pp(results)









