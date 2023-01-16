from collections import Counter
import re
from pprint import pprint

d = {}
with open('edited_log.txt') as log:
    lines = [line for line in log.readlines() if line.startswith('INFO')]
prog = re.compile('INFO:root:(\S*).*of users: (\d*)')
for line in lines:
    server, users = prog.match(line).groups()
    d[server] = int(users)

counter = Counter()
with open('new_urls.txt') as f:
    for line in f:
        server = line.split('/')[2]
        counter[server] += 1

for s, cnt in counter.most_common():
    print(f'{s:24s} {cnt}  total users: {d.get(s, "unknown")}')

