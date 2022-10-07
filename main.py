import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import asyncio
import youtube_dl
import requests
from lyricsgenius import Genius


import utilities

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='~', intents=intents, help_command=None)
genius = Genius(access_token=os.getenv('GENIUS_TOKEN'), remove_section_headers=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='~help'))


@bot.event
async def on_command_error(ctx, error):
    print(f'Error: {error}')


@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        # Exiting if the bot it's not connected to a voice channel
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


# YouTube is a bitch and tries to disconnect our bot from its servers. Use this to reconnect instantly.
# (Because of this disconnect/reconnect cycle, sometimes you will listen a sudden and brief stop)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# List with all the sessions currently active.
# TODO: Terminate season after X minutes have passed without interaction.
sessions = []


############Some Functions###################################################################################

def check_session(ctx):
    """
    Checks if there is a session with the same characteristics (guild and channel) as ctx param.
    :param ctx: discord.ext.commands.Context
    :return: session()
    """
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


def prepare_continue_queue(ctx):
    """
    Used to call next song in queue.
    Because lambda functions cannot call async functions, I found this workaround in discord's api documentation
    to let me continue playing the queue when the current song ends.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    fut = asyncio.run_coroutine_threadsafe(continue_queue(ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)


async def continue_queue(ctx):
    """
    Check if there is a next in queue then proceeds to play the next song in queue.
    As you can see, in this method we create a recursive loop using the prepare_continue_queue to make sure we pass
    through all songs in queue without any mistakes or interaction.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
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


############-COMMANDS-#########################################################################################

############-MUSIC COMMANDS-###################################################################################

############-PLAY COMMAND_#####################################################################################

@bot.command(name='play')
async def play(ctx, *, arg):
    """
    Checks where the command's author is, searches for the music required, joins the same channel as the command's
    author and then plays the audio directly from YouTube.
    :param ctx: discord.ext.commands.Context
    :param arg: str
        arg can be url to video on YouTube or just as you would search it normally.
    :return: None
    """
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
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)
    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
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
        voice.play(source, after=lambda ee: prepare_continue_queue(ctx))


############-SKIP COMMAND-#####################################################################################

@bot.command(name='next', aliases=['skip'])
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    # Finds author's session.
    session = check_session(ctx)
    # If there isn't any song to be played next, return.
    if not session.q.theres_next():
        await ctx.send("No more songs are in the queue")
        return

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=session.guild)

    # If it is playing something, stops it. This works because of the "after" argument when calling voice.play as it is
    # a recursive loop and the current song is already going to play the next song when it stops.
    if voice.is_playing():
        voice.stop()
        return
    else:
        # If nothing is playing, finds the next song and starts playing it.
        session.q.next()
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return


############-QUEUE COMMAND-####################################################################################

@bot.command(name='queue')
async def queue(ctx):
    """
    A debug command to find session id, what is current playing and what is on the queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
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


############-LEAVE COMMAND-####################################################################################

@bot.command(name='leave', aliases=["quit", "fuckoff", "disconnect"])
async def leave(ctx):
    """
    If bot is connected to a voice channel, it leaves it.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected:
        check_session(ctx).q.clear_queue()
        await voice.disconnect()
    else:
        await ctx.send("The bot is not connected")


############-PAUSE COMMAND-####################################################################################

@bot.command(name='pause')
async def pause(ctx):
    """
    If playing audio, pause it.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("I am not playing anything")


############-RESUME COMMAND-###################################################################################

@bot.command(name='resume')
async def resume(ctx):
    """
    If audio is paused, resumes playing it.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused:
        voice.resume()
    else:
        await ctx.send("Music is not paused")


############-STOP COMMAND-#####################################################################################

@bot.command(name='stop')
async def stop(ctx):
    """
    Stops playing audio and clears the session's queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing:
        voice.stop()
        session.q.clear_queue()
    else:
        await ctx.send("Theres nothing to stop")

############-LYRICS COMMAND-###################################################################################

@bot.command(name='lyrics')
async def lyrics(ctx, *args):
    args = ' '.join(args)
    songs = genius.search_songs(args)['hits']
    song = genius.search_song(song_id=songs[0]['result']['id'], artist=songs[0]['result']['artist_names'])

    embed_to_send = discord.Embed(
        title=songs[0]['result']['title'],
        description=song.lyrics.removesuffix('You might also like')
    )

    await ctx.send(embed=embed_to_send)


bot.run(os.getenv('TOKEN'))
