from pathlib import Path

p = Path('log')
for fn in p.glob('*.*'):
    with open(fn) as f:
        lines = f.read().splitlines()
        if len(lines) == 1:
            print(lines)