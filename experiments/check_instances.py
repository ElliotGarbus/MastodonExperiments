import json

instances = []
lines = []
with open('../instance_info.txt') as f:
    for line in f:
        d = json.loads(line)
        instances.append(d['uri'])
        lines.append(line)
# in_set = set(instances)
# print(f'{len(instances)=} {len(in_set)=}')
# instances = list(set(instances))  # remove duplicates
# instances.sort()
# for i in instances:
#     print(i)
lines.sort()
print(f'{len(lines)=} {len(set(lines))=}')
for l0, l1 in zip(lines[::2], lines[1::2]):
    if l0 == l1:
        print(l0)




