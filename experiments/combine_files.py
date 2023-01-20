import json
from pathlib import Path

update_path = Path('all_users.txt')
update_path.unlink(missing_ok=True)

unique_url = set()
with open('users.txt') as new_file, \
     open('users_old.txt') as old_file, \
     open(update_path, 'a') as update_file, \
     open('new_urls.txt', 'w') as new_urls_file:

    # create a unique dict using the new file...
    for line in new_file:
        jl = json.loads(line)
        if jl['url'] not in unique_url:
            unique_url.add(jl['url'])
            update_file.write(line) # copy new file to update file
    new_records = len(unique_url)
    print(f'Records in new file: {new_records}')

    for line in old_file:
        jl = json.loads(line)
        if jl['url'] not in unique_url: # if old entry is not in new entery, add the line to update file
            unique_url.add(jl['url'])
            new_urls_file.write(jl['url'] + '\n')
            update_file.write(line)  # append to update file

    total_records = len(unique_url)
    print(f'Total records: {total_records}; {total_records - new_records} added')



