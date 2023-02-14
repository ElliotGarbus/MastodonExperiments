with open('zero_peers.txt') as f:
    peers = f.readlines()

clean = [p for p in peers if not p.startswith('CQIA4VV2')]

with open('cleaned_zero_peers.txt', 'w') as f:
    for i in clean:
        f.writelines(clean)