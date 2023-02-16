print('reading data...', end='')
with open('zero_peers.txt') as f:
    peers = f.readlines()
print('data read')
clean = [p for p in set(peers) if not any([p.endswith('.cispa.saarland\n'),
                                           p.endswith('.ngrok.io\n'),
                                           p.endswith('.local\n'),
                                           ':' in p,
                                           ])]
print('Cleaned')
clean.sort()
print('sorted')
with open('cleaned_zero_peers.txt', 'w') as f:
    f.writelines(clean)
print('written')

