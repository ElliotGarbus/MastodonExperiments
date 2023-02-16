with open('unknowns.txt') as f:
    data = f.read().splitlines()

cap_start = [d for d in data if d.split('.')[0].isupper()]
print(f'{len(cap_start)=}')

colons = [d for d in data if ':' in d]
print(f'{len(colons)=}')

long_start = [d for d in data if len(d.split('.')[0]) >= 40]
print(f'{len(long_start)=}')
# for ls in long_start:
#     print(ls)

# one_char = [d for d in data if len(d) == 1]
# print(f'{len(one_char)=}')
# print(one_char)


# filter
filtered = [d for d in data if not any((d.split('.')[0].isupper(),
                                        ':' in d,
                                        len(d.split('.')[0]) >= 40,
                                        len(bytes(d, 'utf-8').decode('unicode_escape')) == 1,
                                        ))]
print(len(filtered))
# for f in filtered:
#     print(f)

filtered.sort(key=len)
print(filtered[1:100])
encoded = [f for f in filtered if not len(bytes(f, 'utf-8').decode('unicode_escape'))==1]
encoded.sort(key=len)
print(encoded)