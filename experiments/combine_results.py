from pathlib import Path
import json
from pprint import pprint

all_users = []
p = Path('saved/results')
for fn in p.glob('*.*'):
    with open(fn) as f:
        for line in f:
            jl = json.loads(line)
            all_users.append((jl['url'], jl['followers_count']))
all_users.sort(key=lambda x: x[1], reverse=True)
pprint(all_users[:100])
