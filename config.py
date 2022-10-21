import os
import json

discord_token = None
genius_token = None
spotify_id = None
spotify_secret = None

with open('config.json') as config_file:
    config = json.load(config_file)

if 'tokens' in config.keys():
    discord_token = config['tokens']['discord_token']
    if 'genius_token' in config['tokens'].keys():
        genius_token = config['tokens']['genius_token']
    if 'spotify_secret' in config['tokens'].keys() and 'spotify_id' in config['tokens'].keys():
        spotify_secret = config['tokens']['spotify_secret']
        spotify_id = config['tokens']['spotify_id']
else:
    discord_token = os.environ['discord_token']
    if 'genius_token' in os.environ:
        genius_token = os.environ['genius_token']
    if'spotify_secret' in os.environ and 'spotify_id' in os.environ:
        spotify_secret = os.environ['spotify_secret']
        spotify_id = os.environ['spotify_id']

prefix = config['prefix']
spam_settings = config['spam_settings']
word_blacklist = config['word_blacklist']
level_system = config['level_system']
