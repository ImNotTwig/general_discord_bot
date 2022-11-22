import asyncio
import discord
import yt_dlp
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from lyricsgenius import Genius
from urlextract import URLExtract

from config import config
from colors import colors
from cogs.Music.song_queue import Queue
from cogs.Music.song_queue import Song
from cogs.Music.song_queue import YTDLP_OPTIONS

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

# use this to check if a string contains a url or not
url_extract = URLExtract()

############-MUSIC COMMANDS-###################################################################################

queue_dict = {}


def search(arg):
    # checking if theres a url in the arg and if there is sending that through ytdlp normally
    # if theres not a url then search youtube
    url = url_extract.find_urls(arg)
    if url != []:
        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = ydl.extract_info(url[0], download=False)
    else:
        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)
    return info


def get_songs(arg, song_list, ctx):
    title_list = []
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
        info = search(arg)

        if 'entries' in info.keys():
            for entry in info['entries']:
                song_list.append(entry['url'])

    return (song_list, title_list)


async def get_voice(ctx, bot):
    try:
        voice_channel = ctx.author.voice.channel
    # if author is not in a voice channel this will run
    except AttributeError:
        return None

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

    return voice


class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-PLAYNEXT COMMAND-#################################################################################

    @commands.command(name="playnext", aliases=["pn"], case_insensitive=True)
    async def playnext(self, ctx, *arg):
        arg = ' '.join(arg)
        title_list = []

        voice = await get_voice(ctx, self.bot)
        if not voice:
            await ctx.channel.send("You are not in a voice channel.")
            return

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
        song_list, title_list = get_songs(arg, song_list, ctx)

        if song_list == []:
            info = search(arg) 
            if 'entries' in info.keys():
                for entry in info['entries']:
                    await asyncio.sleep(.1)

                    song = Song(
                        title=entry['title'],
                        url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    title_list.append(entry['title'])
                    break

            else:
                song = Song(
                    title=info['title'],
                    url=info['webpage_url'],
                    number_in_queue=queue_dict[ctx.guild.id].len() + 1
                )
                title_list.append(entry['title'])

        for song in song_list:
            await asyncio.sleep(.1)
            info = search(song)

            if 'entries' in info.keys():
                for entry in info['entries']:
                    await asyncio.sleep(.1)

                    song = Song(
                        title=entry['title'],
                        url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )

                    title_list.append(entry['title'])
                    break

            else:
                song = Song(
                    title=info['title'],
                    url=info['webpage_url'],
                    number_in_queue=queue_dict[ctx.guild.id].len() + 1
                )
                title_list.append(info['title'])
            break

        queue_place = queue_dict[ctx.guild.id].current_pos + 1

        queue_dict[ctx.guild.id].songs.insert(queue_place, song)
        queue_dict[ctx.guild.id].validate_track_order()
        await queue_dict[ctx.guild.id].check_if_playing()

        await ctx.reply(f"{title_list[0]} will play next in the queue.", mention_author=False)

############-PLAY COMMAND-#####################################################################################

    @commands.command(name="play", aliases=["p"], case_insensitive=True)
    async def play(self, ctx, *, arg=None):
        title_list = []

        voice = await get_voice(ctx, self.bot)
        if not voice:
            await ctx.channel.send("You are not in a voice channel.")
            return

        if ctx.guild.id not in queue_dict:
            queue_dict[ctx.guild.id] = Queue(
                songs=[],
                current_pos=0,
                loop=False,
                voice=voice,
                bot=self.bot,
                ctx=ctx
            )

        if arg is None or arg.isspace():
            if voice.is_paused():
                voice.resume()
                await ctx.send("The queue has been un-paused.")
            else:
                await ctx.send("The queue is not paused.")
            return

        song_list = []
        song_list, title_list = get_songs(arg, song_list, ctx)

        if song_list == []:
            info = search(arg) 
            try:
                for entry in info['entries']:
                    await asyncio.sleep(.1)
                    song = Song(
                        title=entry['title'],
                        url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    queue_dict[ctx.guild.id].enqueue(song)
                    title_list.append(entry['title'])

            except KeyError:
                song = Song(
                    title=info['title'],
                    url=info['webpage_url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                    number_in_queue=queue_dict[ctx.guild.id].len() + 1
                )
                queue_dict[ctx.guild.id].enqueue(song)
                title_list.append(info['title'])

        else:
            for song in song_list:
                await asyncio.sleep(.1)
                info = search(song)

                try:
                    for entry in info['entries']:
                        await asyncio.sleep(.1)

                        song = Song(
                            title=entry['title'],
                            url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )

                        queue_dict[ctx.guild.id].enqueue(song)
                        title_list.append(entry['title'])

                except KeyError:
                    song = Song(
                        title=info['title'],
                        url=info['webpage_url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    queue_dict[ctx.guild.id].enqueue(song)
                    title_list.append(info['title'])

                await queue_dict[ctx.guild.id].check_if_playing()

        await queue_dict[ctx.guild.id].check_if_playing()

        embed_desc = '\n'.join(
            f'{x}'
            for x in title_list)

        embed_to_send = discord.Embed(
            title="Songs Added to Queue",
            description=embed_desc,
            color=colors.blurple
        )
        await ctx.reply(embed=embed_to_send, mention_author=False)

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

############-CLEAR COMMAND-####################################################################################

    @commands.command(name="clear")
    async def clear(self, ctx):
        voice = await get_voice(ctx, self.bot)

        if voice:
            queue_dict[ctx.guild.id].clear()
            voice.stop()
            await ctx.channel.send("The queue has been cleared.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

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

        voice = await get_voice(ctx, self.bot)
        if voice:
            if voice.is_paused() is False:
                voice.pause()
                await ctx.send("The player has been paused.")
            else:
                await ctx.send("The player is already paused.")
        else:
            await ctx.send("You are not in a voice channel.")

############-UNPAUSE COMMAND-##################################################################################

    @commands.command(name="unpause", aliases=["resume"], case_insensitive=True)
    async def unpause(self, ctx):
        voice = await get_voice(ctx, self.bot)
        if voice:
            voice.resume()
            await ctx.send("The queue has been un-paused.")
        else:
            await ctx.send("You are not in a voice channel.")

############-SKIP COMMAND-#####################################################################################

    @commands.command(name="next", aliases=["skip"], case_insensitive=True)
    async def next(self, ctx):
        voice = await get_voice(ctx, self.bot)
        if voice:
            voice.stop()
            await ctx.channel.send("Skipped the current song.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-GOTO COMMAND-#####################################################################################

    @commands.command(name="goto", aliases=["jumpto"], case_insensitive=True)
    async def goto(self, ctx, arg: int):
        voice = await get_voice(ctx, self.bot)

        if voice:
            queue_dict[ctx.guild.id].move_to(arg)
            await ctx.channel.send(f"Skipped to {arg} in queue.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-LEAVE COMMAND-####################################################################################

    @commands.command(name="leave", aliases=["fuckoff", "disconnect", "quit", "stop"], case_insensitive=True)
    async def leave(self, ctx):
        voice = await get_voice(ctx, self.bot)
        await voice.disconnect()
        del queue_dict[ctx.guild.id]
        await ctx.send("The bot has left the voice channel, and the queue has been cleared.")

############-REMOVE COMMAND-###################################################################################

    @commands.command(name="remove", case_insensitive=True)
    async def remove(self, ctx, arg: int):
        voice = await get_voice(ctx, self.bot)
        if voice:
            if arg == queue_dict[ctx.guild.id].current().number_in_queue:
                await ctx.channel.send("You can't remove the currently playing song.")
                return

            removed_song = queue_dict[ctx.guild.id].songs.pop(arg - 1)

            if arg - 1 < queue_dict[ctx.guild.id].current_pos:
                queue_dict[ctx.guild.id].current_pos += 1

            queue_dict[ctx.guild.id].validate_track_order()    
            await ctx.channel.send(f"Removed {removed_song.title} from the queue.")
        else:
            await ctx.channel.send("You are not in a voice channel.")
