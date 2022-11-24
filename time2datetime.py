from datetime import datetime, timezone

t = '2022-11-24T00:05:00.346145Z'

reset_time = datetime.fromisoformat(t)
print(reset_time)
last_reset_time = datetime.now(timezone.utc)
print(f'{last_reset_time.tzinfo=}')
print(f'{reset_time.tzinfo=}')
last_reset_time = max(last_reset_time, reset_time)
print(f'last_reset_time=')

print(f'last_reset_time:\t{last_reset_time:%H:%M:%S}')
print(f'now:\t\t\t\t{datetime.now(timezone.utc):%H:%M:%S}')