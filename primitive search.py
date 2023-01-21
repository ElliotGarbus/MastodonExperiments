from pathlib import Path
import json
import webbrowser

def get_user():
    p = Path('results')
    for fn in p.glob('*.*'):
        with open(fn) as f:
            for line in f:
                jl = json.loads(line)
                yield jl

search_term = 'tags/python'
results = []
for user in get_user():
    if search_term.lower() in user['note'].lower():
        results.append(user)
print(f'{len(results)} found')
results.sort(key=lambda u: int(u["followers_count"]), reverse=True)
counter = 0
for user in results:
    counter += 1
    webbrowser.open(user['url'])
    if not (counter % 10):
        r = input('Continue? [y/n]').lower()
        if r == 'n':
            break


