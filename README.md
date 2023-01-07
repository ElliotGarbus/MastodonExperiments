# MastodonExperiments
Fooling around with async/Trio and the Mastodon API

Access Multiple Servers to access thier directory data, uses 2 files below:
- from_servers - main driver program, gets a list of instances, and calls get_users_async
- get_instances.py - gets a list of mastodon instances
- get_users_async - gets directory data from an instance, stores results and logs

experiments directory - obsolete experiements/prototypes for learning
- find_most_popular - for the 100 users with the greatest number of followers, opens thier profile 10 at a time
  - gets passed a file of directory records
- mastodon-experiments.py - first simple use of the API, this is junk.
- search_server.py - send a search request to an instance, uses mastodon.py
- time_to_datatime - test convering the time in the headers
- trio_play.py first 
