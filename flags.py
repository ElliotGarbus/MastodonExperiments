"""
Constants that control rarely changed functionality, and the user-agent header
"""

INSTANCE_API_VERSION = 'v1'  # select v1 or v2 of the api, will change when v1 is no longer supported
IGNORE_EMOJI_URL = True  # used to ignore the emoji urls...
CREATE_GRAPH = False   # create a graph file of the peer server data

try:
    user_agent_header = {'user-agent': os.environ['USERAGENT']}
except KeyError:
    user_agent_header = {}