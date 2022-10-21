import asyncio
import discord
import requests
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from lyricsgenius import Genius
from config import genius_token, spotify_id, spotify_secret

"""
TODO:
- Implement a Queue system
    - queue is a list of dicts that are as follows
    {
    'name': str,
    'url': str,
    'number': int
    }
    - when a song is done playing, play the next song on discord and, remove it from the queue
- Lyric Command
- Shuffle Queue command
- Add a function that takes an argument from the user and returns a list of song urls and titles
"""

############-CONFIGS-##########################################################################################

if genius_token:
    genius = Genius(access_token=genius_token, remove_section_headers=True)
    
if spotify_id and spotify_secret:
    client_credentials_manager = SpotifyClientCredentials(spotify_id, spotify_secret)
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

############-MUSIC COMMANDS-###################################################################################

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot