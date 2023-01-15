# users instances.social api to access a list of servers https://instances.social/api/doc/
import httpx
from mastodon_instances_key import mi_info


"""
format of mi_info
mi_info = {'name':'app_name',
           'app-id':'app_id number',
           'token': 'token string'}
"""



def get_instances(n):
    # returns a list of servers
    header = {'Authorization': 'Bearer ' + mi_info['token'] }
    params = {'count': f'{n}', 'include_down': 'false', 'language': 'en', 'sort_by': 'users', 'sort_order': 'desc'}
    r = httpx.get('https://instances.social/api/1.0/instances/list',headers=header, params=params, timeout=100)
    d = r.json()
    return [instance['name'] for instance in d['instances']]



if __name__ == '__main__':
    n = get_instances(5)
    print(n)

