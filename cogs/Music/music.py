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


def get_songs(arg, ctx):
    """
    This function is to be used to check if the arg is a spotify or soundcloud link

    if that's the case then we will return a list of every song in the playlist/album

    otherwise we return an empty list.
    """
    title_list = []
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
        """
        This command adds a song to the next position in queue

        it will not work when the shuffle is enabled because it 

        would add the song to the next number in queue but it would not play it next 
        """

        arg = ' '.join(arg)
        title_list = []

        voice = await get_voice(ctx, self.bot)
        if not voice:
            await ctx.channel.send("You are not in a voice channel.")
            return

        if ctx.guild.id not in queue_dict:
            queue_dict[ctx.guild.id] = Queue(voice=voice, bot=self.bot, ctx=ctx, songs=[], already_played_tracks=[])

        if queue_dict[ctx.guild.id].shuffle:
            await ctx.channel.send("You can not use this command when shuffle is enabled.")
            return

        song_list, title_list = get_songs(arg, ctx)

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
        """
        This command, given a song/playlist/album will do one of two things:

            if given a spotify or soundcloud link, will get all the urls or the songs in the playlist if soundcloud,

            or get the title and artist of every song in the playlist if spotify, then search yt-dlp for every song individually.

            otherwise it will get every title and url and add it to the queue it will then put it into yt-dlp and add all the songs at once.

        If no argument was given then it will simply check if the player is paused and if so, will unpause it.
        """

        title_list = []

        voice = await get_voice(ctx, self.bot)
        if not voice:
            await ctx.channel.send("You are not in a voice channel.")
            return

        if ctx.guild.id not in queue_dict:
            queue_dict[ctx.guild.id] = Queue(voice=voice, bot=self.bot, ctx=ctx, songs=[], already_played_tracks=[])

        if arg is None or arg.isspace():
            if voice.is_paused():
                voice.resume()
                await ctx.send("The queue has been un-paused.")
            else:
                await ctx.send("The queue is not paused.")
            return

        song_list, title_list = get_songs(arg, ctx)

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
        """
        This command simply returns a list of the songs in the queue with their respective number in queue.

        it does not show the song that will play next when shuffle is enabled.

        if the song is the current playing song it will have a -> next to it.
        """

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
        """
        This command clears the queue and stops the currently playing song. Yes that is all.
        """
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
        """
        This command gives the title and the location in queue of the currently playing song.

        Maybe in the future I will have updated it to show how long the track is and how far we are into it.
        """

        embed_to_send = discord.Embed(
            title="Now playing",
            description=f"""Title: {queue_dict[ctx.guild.id].current().title}
Posistion: {queue_dict[ctx.guild.id].current().number_in_queue}"""
        )

        await ctx.send(embed=embed_to_send)

############-PAUSE COMMAND-####################################################################################

    @commands.command(name="pause", case_insensitive=True)
    async def pause(self, ctx):
        """
        This command paused the queue if the queue is not paused.
        """

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
        """
        This command resumes the queue if the queue is paused.
        """
        voice = await get_voice(ctx, self.bot)
        if voice:
            voice.resume()
            await ctx.send("The queue has been un-paused.")
        else:
            await ctx.send("You are not in a voice channel.")

############-SKIP COMMAND-#####################################################################################

    @commands.command(name="next", aliases=["skip"], case_insensitive=True)
    async def next(self, ctx):
        """
        This command skips to the next song in the queue

        it also works when the shuffle is enabled.
        """
        voice = await get_voice(ctx, self.bot)
        if voice:
            voice.stop()
            await ctx.channel.send("Skipped the current song.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-GOTO COMMAND-#####################################################################################

    @commands.command(name="goto", aliases=["jumpto"], case_insensitive=True)
    async def goto(self, ctx, arg: int):
        """
        This command will go to the specified song in the queue.

        Again that is all.
        """
        voice = await get_voice(ctx, self.bot)

        if voice:
            queue_dict[ctx.guild.id].move_to(arg)
            await ctx.channel.send(f"Skipped to {arg} in queue.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-LEAVE COMMAND-####################################################################################

    @commands.command(name="leave", aliases=["fuckoff", "disconnect", "quit", "stop"], case_insensitive=True)
    async def leave(self, ctx):
        """
        Another simple command. 

        This one makes the bot clear the queue and leave the voice channel.
        """
        voice = await get_voice(ctx, self.bot)
        await voice.disconnect()
        del queue_dict[ctx.guild.id]
        await ctx.send("The bot has left the voice channel, and the queue has been cleared.")

############-REMOVE COMMAND-###################################################################################

    @commands.command(name="remove", case_insensitive=True)
    async def remove(self, ctx, arg: int):
        """
        This command removes a specified song in the queue.

        it does this by using an index specified by the user.
        """
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

############-LOOP COMMAND-#####################################################################################

    @commands.command(name="loop", case_insensitive=True)
    async def loop(self, ctx):
        """
        This command turns the loop on for the queue if off.

        It will turn the loop off it is on.
        """
        voice = await get_voice(ctx, self.bot)
        if voice:
            if queue_dict[ctx.guild.id].loop is False:
                queue_dict[ctx.guild.id].loop = True
                await ctx.channel.send("Turned the loop on.")
            else:
                queue_dict[ctx.guil.did].loop = False
                await ctx.channel.send("Turned the loop off.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-SHUFFLE COMMAND-##################################################################################

    @commands.command(name="shuffle", case_insensitive=True)
    async def shuffle(self, ctx):
        """
        This command will turn the shuffle on if it is off.

        it will turn it off, if it is on.
        """
        voice = await get_voice(ctx, self.bot)
        if voice:
            if queue_dict[ctx.guild.id].shuffle is False:
                queue_dict[ctx.guild.id].shuffle = True
                await ctx.channel.send("Turned shuffle on.")
            else:
                queue_dict[ctx.guil.id].shuffle = False
                await ctx.channel.send("Turned shuffle off.")
        else:
            await ctx.channel.send("You are not in a voice channel.")

############-LYRICS COMMAND-###################################################################################

    @commands.command(name='lyrics', aliases=['lyric'], case_insensitive=True)
    async def lyrics(self, ctx, *, args=None):
        """
        This command will show the lyrics to the currently playing song if no argument is given

        if an argument is given it will search for the lyrics of the argument.

        It uses the Genius api to do this.
        """
        if args is None:
            if queue_dict[ctx.guild.id]:
                args = queue_dict[ctx.guild.id].current().title
            else:
                await ctx.channel.send("No song is playing and no title was given.")

        args = ' '.join(args)
        songs = genius.search_songs(args)['hits']
        song = genius.search_song(song_id=songs[0]['result']['id'], artist=songs[0]['result']['artist_names'])

        embed_to_send = discord.Embed(
            title=songs[0]['result']['title'],
            description=song.lyrics.removesuffix('You might also like')
        )

        await ctx.send(embed=embed_to_send)
