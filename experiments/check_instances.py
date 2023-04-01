import json

with open('../instance_info.txt') as f:
    for line in f:
        d = json.loads(line)
        print(d['uri'])
