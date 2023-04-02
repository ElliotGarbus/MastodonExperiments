import json

instances = []
with open('../instance_info.txt') as f:
    for line in f:
        d = json.loads(line)
        instances.append(d['uri'])
in_set = set(instances)
print(f'{len(instances)=} {len(in_set)=}')
instances = list(set(instances))  # remove duplicates
instances.sort()
for i in instances:
    print(i)



