from pathlib import Path

p = Path('../log')
for fn in p.glob('*.*'):
    with open(fn) as f:
        for line in f:
            if 'Error' in line:
                print(line)