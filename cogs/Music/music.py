import asyncio
import discord
import requests
import youtube_dl
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

if "tokens" in config.keys():
    genius = Genius(access_token=config['tokens']['genius_token'], remove_section_headers=True)
else:
    token = os.getenv('genius_token')
    genius = Genius(access_token=token, remove_section_headers=True)

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
        await ctx.send("The queue is empty")
        return

    session.q.next()

    voice = discord.utils.get(bot.voice_clients, guild=session.guild)
    source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

    if voice.is_playing():
        voice.stop()

    session.q.queue.pop(0)

    voice.play(source, after=lambda e: prepare_continue_queue(ctx))
    await ctx.send(f"Now playing: {session.q.current_music.title}")
    await ctx.send(f"""<{session.q.current_music.webpage_url}>
    Now playing: {session.q.current_music.title}""")

############-MUSIC COMMANDS-###################################################################################

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-PLAY COMMAND_#####################################################################################

    @commands.command(name='play')
    async def play(self, ctx, *, arg):
        try:
            voice_channel = ctx.author.voice.channel

        # If command's author isn't connected, return.
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel")
            return

        # Finds author's session.
        session = check_session(ctx)

        # Searches for the video
        with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
            try:
                requests.get(arg)
            except Exception as e:
                print(e)
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                    'entries'][0]
            else:
                info = ydl.extract_info(arg, download=False)

        url = info['formats'][0]['url']
        webpage_url = info['webpage_url']
        title = info['title']

        session.q.enqueue(title, url, webpage_url)

        # Finds an available voice client for the bot.
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)
        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        # If it is already playing something, adds to the queue
        if voice.is_playing():
            await ctx.send(f"""<{webpage_url}>
    Added to queue: {title}""")
            return
        else:
            await ctx.send(f"""<{webpage_url}>
    Added to queue: {title}""")

            # Guarantees that the requested music is the current music.
            session.q.set_last_as_current()

            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            voice.play(source, after=lambda ee: (prepare_continue_queue(self.bot, ctx), session.q.pop[0]))

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
            if session.q.theres_next() == False:
                session.q.clear_queue()
                return

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
        # await ctx.send(f"Session ID: {session.id}")
        await ctx.send(f"Current song: {session.q.current_music.title}")
        queue = [q[0] for q in session.q.queue]
        embed_desc = '\n'.join(
            ''.join(x)
            for x in queue)
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
        queue.pop(arg)
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
