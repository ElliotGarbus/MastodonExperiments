print('reading data...', end='')
with open('zero_peers.txt') as f:
    peers = f.readlines()
print('data read')
clean = [p for p in set(peers) if not any([p.endswith('.cispa.saarland\n'),
                                           p.endswith('.ngrok.io\n'),
                                           p.endswith('.local\n'),
                                           p.endswith('activitypub-troll.cf\n'),
                                           p.endswith('misskey-forkbomb.cf\n'),
                                           p.endswith('repl.co\n'),
                                           p.endswith('gab.best\n'),
                                           p.startswith("192."),
                                           ':' in p,
                                           '..' in p,
                                           '.' not in p,
                                           len(p.split('.')[0]) >= 40,
                                           p.split('.')[0].isupper(),
                                           ])]
print('Cleaned')
clean.sort()
print('sorted')
with open('cleaned_zero_peers.txt', 'w') as f:
    f.writelines(clean)
print('written')

