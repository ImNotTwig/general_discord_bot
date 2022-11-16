import asyncio
import discord
import requests
import yt_dlp
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from lyricsgenius import Genius
from config import config
from cogs.Music.song_queue import Queue
from cogs.Music.song_queue import Song

YTDLP_OPTIONS = {
    'fragment_count': '64',
    'extract_flat': True,
    'format': 'bestaudio/best',
    'downloader': 'aria2c',
    'skip_download': True,
    'dump_single_json': True
}

############-CONFIGS-##########################################################################################

if config.tokens.genius_token:
    genius = Genius(access_token=config.tokens.genius_token,
                    remove_section_headers=True)

if not config.tokens.spotify_id:
    config.tokens.spotify_id = os.getenv('spotify_id')
    config.tokens.spotify_secret = os.getenv('spotify_secret')

if config.tokens.spotify_id and config.tokens.spotify_secret:
    client_credentials_manager = SpotifyClientCredentials(
        config.tokens.spotify_id, config.tokens.spotify_secret)
    spotify = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager)
else:
    print("Spotify could not be initialized, if you want spotify support please input your credentials into the config file")

############-MUSIC COMMANDS-###################################################################################

queue_dict = {}


class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-PLAY COMMAND-#####################################################################################

    @commands.command(name="play", case_insensitive=True)
    async def play(self, ctx, *arg):

        arg = ' '.join(arg)

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if ctx.guild.id not in queue_dict:
            queue_dict[ctx.guild.id] = Queue(
                songs=[],
                current_pos=0,
                loop=False,
                voice=voice,
                bot=self.bot,
                ctx=ctx
            )

        song_list = []
        if arg.startswith("https://open.spotify.com/playlist"):
            for i in spotify.playlist(playlist_id=arg)['tracks']['items']:
                song = f"{i['track']['name']} - {i['track']['album']['artists'][0]['name']}"
                song_list.append(song)

        elif arg.startswith("https://open.spotify.com/album"):
            for i in spotify.album(arg)['tracks']['items']:
                song = f"{i['name']} - {i['artists'][0]['name']}"
                song_list.append(song)

        elif arg.startswith("https://open.spotify.com/track"):
            track = spotify.track(track_id=arg)
            song = f"{track['name']} - {track['album']['artists'][0]['name']}"
            song_list.append(song)

        elif arg.startswith("https://soundcloud"):
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                try:
                    requests.get(arg)
                except Exception as e:
                    print(e)
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                else:
                    info = ydl.extract_info(arg, download=False)

                if 'entries' in info.keys():
                    for entry in info['entries']:
                        await asyncio.sleep(.1)
                        try:
                            requests.get(entry['url'])
                        except Exception as e:
                            print(e)
                            song_info = ydl.extract_info(f"ytsearch:{entry['url']}", download=False)
                        else:
                            song_info = ydl.extract_info(entry['url'], download=False)

                        entry['title'] = song_info['title']
                            
                        song = Song(
                            title=entry['title'],
                            url=entry['url'],
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )
                        queue_dict[ctx.guild.id].enqueue(song)

                        if voice.is_playing() is True:
                            pass
                        else:
                            if queue_dict[ctx.guild.id].end_of_queue is True:
                                await queue_dict[ctx.guild.id].play_last()
                            else:
                                await queue_dict[ctx.guild.id].play_next()
                                queue_dict[ctx.guild.id].voice.resume()
            

        # handling youtube links and searches
        else:
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                try:
                    requests.get(arg)
                except Exception as e:
                    print(e)
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                else:
                    info = ydl.extract_info(arg, download=False)

                if 'entries' in info.keys():
                    for entry in info['entries']:
                        await asyncio.sleep(.1)

                        song = Song(
                            title=entry['title'],
                            url=entry['url'].removesuffix(
                                '#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )

                        queue_dict[ctx.guild.id].enqueue(song)

                else:
                    song = Song(
                        title=info['title'],
                        url=info['webpage_url'],
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    queue_dict[ctx.guild.id].enqueue(song)

        if song_list != []:
            for song in song_list:
                with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                    try:
                        requests.get(song)
                    except Exception as e:
                        print(e)
                        info = ydl.extract_info(
                            f"ytsearch:{song}", download=False)
                    else:
                        info = ydl.extract_info(song, download=False)

                    if 'entries' in info.keys():
                        for entry in info['entries']:
                            await asyncio.sleep(.1)

                            song = Song(
                                title=entry['title'],
                                url=entry['url'].removesuffix(
                                    '#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                                number_in_queue=queue_dict[ctx.guild.id].len(
                                ) + 1
                            )

                            queue_dict[ctx.guild.id].enqueue(song)

                    else:
                        song = Song(
                            title=info['title'],
                            url=info['webpage_url'],
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )
                        queue_dict[ctx.guild.id].enqueue(song)
                    if voice.is_playing() is True:
                        pass
                    else:
                        if queue_dict[ctx.guild.id].end_of_queue is True:
                            await queue_dict[ctx.guild.id].play_last()
                        else:
                            await queue_dict[ctx.guild.id].play_next()
                        queue_dict[ctx.guild.id].voice.resume()

        if voice.is_playing() is True:
            pass
        else:
            if queue_dict[ctx.guild.id].end_of_queue is True:
                await queue_dict[ctx.guild.id].play_last()
            else:
                await queue_dict[ctx.guild.id].play_next()
            queue_dict[ctx.guild.id].voice.resume()

############-QUEUE COMMAND-####################################################################################

    @commands.command(name="queue", aliases=["q"], case_insensitive=True)
    async def queue(self, ctx):

        embed_list = []

        if ctx.guild.id in queue_dict:
            for x in queue_dict[ctx.guild.id].songs:
                if x.number_in_queue == queue_dict[ctx.guild.id].current_pos:
                    embed_list.append(f'-> {x.number_in_queue} - {x.title}')
                else:
                    embed_list.append(f'{x.number_in_queue} - {x.title}')

            embed_desc = '\n'.join(
                f'{x}'
                for x in embed_list)

            embed_to_send = discord.Embed(
                title="Queue",
                description=embed_desc
            )
            await ctx.send(embed=embed_to_send)
        else:
            await ctx.send("Nothing is playing.")

############-NOWPLAYING COMMAND-###############################################################################

    @commands.command(name="nowplaying", aliases=["np"], case_insensitive=True)
    async def nowplaying(self, ctx):

        embed_to_send = discord.Embed(
            title="Now playing",
            description=f"""Title: {queue_dict[ctx.guild.id].current().title}
Posistion: {queue_dict[ctx.guild.id].current().number_in_queue}"""
        )

        await ctx.send(embed=embed_to_send)

############-PAUSE COMMAND-####################################################################################

    @commands.command(name="pause", case_insensitive=True)
    async def pause(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if voice.is_paused() is False:
            voice.pause()
            await ctx.send("The player has been paused.")
        else:
            await ctx.send("The player is already paused.")

############-UNPAUSE COMMAND-##################################################################################

    @commands.command(name="unpause", aliases=["resume"], case_insensitive=True)
    async def unpause(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        voice.resume()
        await ctx.send("The queue has been un-paused.")

############-SKIP COMMAND-#####################################################################################

    @commands.command(name="next", aliases=["skip"], case_insensitive=True)
    async def next(self, ctx):
        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await ctx.channel.send("Skipped the current song.")

        voice.stop()
        await queue_dict[ctx.guild.id].play_next()

############-GOTO COMMAND-#####################################################################################

    @commands.command(name="goto", case_insensitive=True)
    async def goto(self, ctx, arg: int):
        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await queue_dict[ctx.guild.id].move_to(arg)

        await ctx.channel.send(f"Skipped to {arg} in queue.")

############-LEAVE COMMAND-####################################################################################

    @commands.command(name="leave", aliases=["fuckoff", "disconnect", "quit", "stop"], case_insensitive=True)
    async def leave(self, ctx):
        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await voice.disconnect()
        del queue_dict[ctx.guild.id]

        await ctx.send("The bot has left the voice channel, and the queue has been cleared.")

############-REMOVE COMMAND-###################################################################################

    @commands.command(name="remove", case_insensitive=True)
    async def remove(self, ctx, arg: int):
        if arg == queue_dict[ctx.guild.id].current().number_in_queue:
            await ctx.channel.send("You can't remove the currently playing song.")
            return
        removed_song = queue_dict[ctx.guild.id].songs.pop(arg - 1)
        a = 1
        for i in queue_dict[ctx.guild.id].songs:
            i.number_in_queue = a
            a += 1
        await ctx.channel.send(f"Removed {removed_song.title} from the queue.")
