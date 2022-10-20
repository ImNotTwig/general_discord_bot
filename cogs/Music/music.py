import asyncio
import discord
import requests
import yt_dlp
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from lyricsgenius import Genius
import json
import os

from cogs.Music import utilities

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

with open("config.json", 'r+', encoding="utf8") as file:
    config = json.load(file)

spotify_id = False
spotify_secret = False

if "tokens" in config.keys():
    genius = Genius(access_token=config['tokens']['genius_token'], remove_section_headers=True)
    
    if "spotify_id" in config['tokens'].keys():
        spotify_id = config['tokens']['spotify_id']
    if "spotify_secret" in config['tokens'].keys():
        spotify_secret = config['tokens']['spotify_secret']
        
    if spotify_id and spotify_secret:
        client_credentials_manager = SpotifyClientCredentials(spotify_id, spotify_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
else:
    token = os.getenv('genius_token')
    genius = Genius(access_token=token, remove_section_headers=True)
    
    spotify_secret = os.getenv('spotify_secret')
    spotify_id = os.getenv('spotify_id')
        
    if spotify_secret and spotify_id is True:
        client_credentials_manager = SpotifyClientCredentials(spotify_id, spotify_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# List with all the sessions currently active.
sessions = []

############-QUEUE FUNCTIONS-##################################################################################

def check_session(ctx):
    if len(sessions) > 0:
        for i in sessions:
            if i.guild == ctx.guild and i.channel == ctx.author.voice.channel:
                return i
        session = utilities.Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = utilities.Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session

def prepare_continue_queue(bot, ctx):
    fut = asyncio.run_coroutine_threadsafe(continue_queue(bot, ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)

async def continue_queue(bot, ctx):
    session = check_session(ctx)
    if not session.q.theres_next():
        await ctx.send("The queue is at the end.")
        return

    session.q.next()

    voice = discord.utils.get(bot.voice_clients, guild=session.guild)
    source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

    if voice.is_playing():
        voice.stop()
    voice.play(source, after=lambda e: prepare_continue_queue(bot, ctx))
    await ctx.send(f"Now playing: {session.q.current_music.title}")

############-MUSIC COMMANDS-###################################################################################

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-PLAY COMMAND_#####################################################################################

    @commands.command(name='play')
    async def play(self, ctx, *, arg):
        arg_list = []
        song_list = []
        try:
            voice_channel = ctx.author.voice.channel

        # If command's author isn't connected, return.
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel")
            return

        # Finds author's session.
        session = check_session(ctx)
        
        # checks if the link is from spotify
        if arg.startswith('https://open.spotify.com') is True:
            # checks if the link is a playlist 
            if arg.startswith('https://open.spotify.com/playlist'):
                for song in spotify.user_playlist_tracks(user="", playlist_id=arg):
                    arg_list.append(f"{song['name']} - {song['album']['artists'][0]['name']}")
            # checks if the link is an album
            elif arg.startswith('https://open.spotify.com/album'):
                for song in spotify.album(arg)['tracks']['items']:
                    arg_list.append(f"{song['name']} - {song['artists'][0]['name']}")
            else:
                arg = spotify.track(track_id=arg)
                arg = f"{arg['name']} - {arg['album']['artists'][0]['name']}"
                arg_list.append(arg)
        else:
            arg_list.append(arg)

        for arg in arg_list:
            # Searches for the video
            with yt_dlp.YoutubeDL({'downloader': 'aria2c', 'skip_download': True}) as ydl:
                try:
                    requests.get(arg)
                except Exception as e:
                    print(e)
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                else:
                    info = ydl.extract_info(arg, download=False)
                    
                # print(info)
                    
                # if it has an entries field
                if 'entries' in info.keys():
                    pass
                else:
                    info['entries'] = [{}]
                    info['entries'][0]['title'] = info['title']
                    # if the song is from soundcloud
                    if arg.startswith('https://soundcloud.com/') is True:
                        info['entries'][0]['requested_formats'] = [{}, {}]
                        info['entries'][0]['requested_formats'][1]['url'] = info['url']
                    # if the song is from a discord attachment
                    elif arg.startswith('https://cdn.discordapp.com/'):
                        info['entries'][0]['requested_formats'] = [{}, {}]
                        info['entries'][0]['requested_formats'][1]['url'] = info['formats'][0]['url']
                    else:
                        info['entries'][0]['requested_formats'] = info['requested_formats']
                    info['entries'][0]['webpage_url'] = info['webpage_url']
            
                for entry in info['entries']:
                    title = entry['title']
                    if 'requested_formats' in entry.keys():
                        url = entry['requested_formats'][1]['url']
                    else:
                        url = entry['url']
                    webpage_url = entry['webpage_url']
                    number = len(session.q.queue) + 1
                
                    song_list.append({'number': number, 'title': title})

                    session.q.enqueue(title, url, webpage_url, number)
            
                    # Finds an available voice client for the bot.
                    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                    await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)
                    if not voice:
                        await voice_channel.connect()
                        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

                    # If it is already playing something, adds to the queue
                    if voice.is_playing():
                        pass
                #        await ctx.send(f"""<{webpage_url}>
                #Added to queue: {title}""")
                    else:
                #        await ctx.send(f"""<{webpage_url}>
                #Added to queue: {title}""")

                        # Guarantees that the requested music is the current music.
                        session.q.set_last_as_current()

                        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                        voice.play(source, after=lambda e: prepare_continue_queue(self.bot, ctx))
                    
                embed_title = "Songs Added"
                embed_desc = '\n'.join(
                    f"{song['number']} - {song['title']}" 
                    for song in song_list)
                
############-SKIP COMMAND-#####################################################################################

    @commands.command(name='next', aliases=['skip'])
    async def skip(self, ctx):
        # Finds author's session.
        session = check_session(ctx)

        # Finds an available voice client for the bot.
        voice = discord.utils.get(self.bot.voice_clients, guild=session.guild)
        # If it is playing something, stops it. This works because of the "after" argument when calling voice.play as it is
        # a recursive loop and the current song is already going to play the next song when it stops.
        if voice.is_playing():
            voice.stop()
            # If there isn't any song to be played next, clear the queue and then return.
            if session.q.theres_next() is False:
                session.q.clear_queue()
                await ctx.channel.send("The queue is empty.")
            return
        else:
            # If nothing is playing, finds the next song and starts playing it.
            session.q.next()
            source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
            voice.play(source, after=lambda e: prepare_continue_queue(self.bot, ctx))
            return

############-QUEUE COMMAND-####################################################################################

    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        session = check_session(ctx)
        queue = [q for q in session.q.queue]
        embed_list = []
        for x in queue:
            if x.number == session.q.current_music.number:
                embed_list.append(f'-> {x.number} - {x.title}')
            else:
                embed_list.append(f'{x.number} - {x.title}')

        embed_desc = '\n'.join(
            f'{x}'
            for x in embed_list)

        embed_to_send = discord.Embed(
            title="Queue",
            description=embed_desc
        )
        await ctx.send(embed=embed_to_send)

############-REMOVE COMMAND-###################################################################################

    @commands.command(name="remove")
    async def remove(self, ctx, *args):
        session = check_session(ctx)
        queue = session.q.queue

        if len(queue) == 0:
            return
        arg = int(args[0]) - 1

        await ctx.send(f"removed {queue[arg][0]} from the queue")
        session.q.queue.pop(arg)
        return

############-LEAVE COMMAND-####################################################################################

    @commands.command(name='leave', aliases=["quit", "fuckoff", "disconnect"])
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected:
            check_session(ctx).q.clear_queue()
            await voice.disconnect()
        else:
            await ctx.send("The bot is not connected")

############-PAUSE COMMAND-####################################################################################

    @commands.command(name='pause')
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send("I am not playing anything")

############-RESUME COMMAND-###################################################################################

    @commands.command(name='resume')
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused:
            voice.resume()
        else:
            await ctx.send("Music is not paused")

############-STOP COMMAND-#####################################################################################

    @commands.command(name='stop')
    async def stop(self, ctx):
        session = check_session(ctx)
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing:
            voice.stop()
            session.q.clear_queue()
        else:
            await ctx.send("Theres nothing to stop")

############-LYRICS COMMAND-###################################################################################

    @commands.command(name='lyrics')
    async def lyrics(self, ctx, *args):
        args = ' '.join(args)
        songs = genius.search_songs(args)['hits']
        song = genius.search_song(song_id=songs[0]['result']['id'], artist=songs[0]['result']['artist_names'])

        embed_to_send = discord.Embed(
            title=songs[0]['result']['title'],
            description=song.lyrics.removesuffix('You might also like')
        )

        await ctx.send(embed=embed_to_send)

###############################################################################################################
