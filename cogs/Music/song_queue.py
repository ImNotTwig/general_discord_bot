import discord
from dataclasses import dataclass
import yt_dlp
import random

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -nostats -loglevel 0'
}
YTDLP_OPTIONS = {
    'concurrent_fragments': '64',
    'extract_flat': True,
    'format': 'bestaudio/best',
    'downloader': 'aria2c',
    'skip_download': True,
    'dump_single_json': True,
    'quiet': True
}


@dataclass
class Song:
    title: str
    url: str
    number_in_queue: int


@dataclass
class Queue:
    voice: discord.VoiceState
    bot: discord.ext.commands.Bot
    ctx: discord.ext.commands.Context
    songs: list
    # this is for the shuffle so we dont play the same song
    # again until its done playing all the songs
    already_played_tracks: list
    current_pos: int = 0
    end_of_queue: bool = False
    shuffle: bool = False
    loop: bool = False

    def len(self):
        return len(self.songs)

    def enqueue(self, song: Song):
        self.songs.append(song)

    def current(self):
        if self.len() != 0:
            return self.songs[self.current_pos - 1]

    def move_to(self, index):
        self.current_pos = index - 1
        self.voice.stop()

    def clear(self):
        self.songs.clear()
        self.voice.stop()

    def validate_track_order(self):
        a = 1
        for i in self.songs:
            i.number_in_queue = a
            a += 1

    async def check_if_playing(self):
        if self.voice.is_playing() is True:
            pass
        else:
            if self.end_of_queue is True:
                await self.play_last()
            else:
                await self.play_next()
            if self.voice.is_paused():
                self.voice.resume()

    async def change_pos(self):
        if self.shuffle is True:
            if self.len() >= len(self.already_played_tracks):
                self.current_pos = random.randint(1, self.len())

                while self.current_pos in self.already_played_tracks:

                    self.current_pos = random.randint(1, self.len())

                    if self.len() == len(self.already_played_tracks):
                        if self.loop is False:
                            self.current_pos = self.len() + 1
                            self.end_of_queue = True
                            self.shuffle = False
                            self.already_played_tracks.clear()
                            await self.ctx.send("Every song has been played, so shuffle has been turned off.")

                self.already_played_tracks.append(self.current_pos)

                already_played_checker = []
                for i in range(1, self.len()):
                    if i in self.already_played_tracks:
                        already_played_checker.append(i)

                if len(already_played_checker) == self.len():
                    self.already_played_tracks.clear()
                    self.current_pos = self.len() + 1
                    self.shuffle = False
                    self.end_of_queue = True
                    await self.ctx.send("Every song has been played, so shuffle has been turned off.")
        else:
            self.current_pos += 1

    # play from the current posistion of the queue

    async def play(self):
        if self.len() != 0:
            # getting the voice channel we are connected to
            voice = discord.utils.get(self.bot.voice_clients, guild=self.ctx.guild)

            # getting the link to stream over ffmpeg
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                info = ydl.extract_info(self.current().url, download=False)

            # the source from ffmpeg to play on the bot
            source = await discord.FFmpegOpusAudio.from_probe(info['url'], **FFMPEG_OPTIONS)

            # playing the music, this also calls the play next function again when its done
            try:
                voice.play(source, after=lambda x: self.bot.loop.create_task(self.play_next()))
            except (discord.errors.ClientException, AttributeError):
                pass

            # send a message for the music that we are now playing
            await self.ctx.send(f"Now playing: {self.current().title}")

            self.voice = voice
        else:
            self.current_pos = 0

    # play the last song in the queue
    async def play_last(self):
        if self.len() != 0:
            self.current_pos = self.len()

            # getting the voice channel we are connected to
            voice = discord.utils.get(self.bot.voice_clients, guild=self.ctx.guild)

            paused = None

            if voice.is_paused():
                paused = True

            # getting the link to stream over ffmpeg
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                info = ydl.extract_info(self.current().url, download=False)

            # the source from ffmpeg to play on the bot
            source = await discord.FFmpegOpusAudio.from_probe(info['url'], **FFMPEG_OPTIONS)

            # playing the music, this also calls this function again when its done
            try:
                voice.play(source, after=lambda x: self.bot.loop.create_task(self.play_next()))
            except (discord.errors.ClientException, AttributeError):
                pass

            if paused is True:
                try:
                    voice.pause()
                except AttributeError:
                    pass

            if voice.is_paused() is False or self.end_of_queue is False:
                # send a message for the music that we are now playing
                await self.ctx.send(f"Now playing: {self.current().title}")

            self.voice = voice
        else:
            self.current_pos = 0

    # play the last song in the queue
    async def play_next(self):
        if self.len() != 0:
            # incrementing the current posistion
            # this is so we can play the *next* song
            # afterall this function is called play_next
            await self.change_pos()

            paused = False

            paused = self.voice.is_paused()

            # checking if we are after the end of the queue or not 
            if self.current_pos >= self.len() + 1:
                # if we are not looping
                if self.loop is False:
                    # pause the queue and pause the discord player
                    self.voice.pause()
                    paused = True
                    if self.end_of_queue is True and self.voice.channel.members != 0:
                        await self.ctx.send("The queue has reached the end. The player has paused.")
                    self.end_of_queue = True
                    # set the current posistion to the song at the end of the queue
                    # this is because when we play a song after this it will play that song
                    self.current_pos = self.len()

                # if we are looping
                if self.loop is True:
                    self.current_pos = 1

            # getting the voice channel we are connected to
            voice = discord.utils.get(self.bot.voice_clients, guild=self.ctx.guild)

            # getting the link to stream over ffmpeg
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                info = ydl.extract_info(self.current().url, download=False)

            # the source from ffmpeg to play on the bot
            source = await discord.FFmpegOpusAudio.from_probe(info['url'], **FFMPEG_OPTIONS)

            # playing the music, this also calls this function again when its done
            try:
                voice.play(source, after=lambda x: self.bot.loop.create_task(self.play_next()))
            except (discord.errors.ClientException, AttributeError):
                pass

            if paused is True:
                try:
                    voice.pause()
                except AttributeError:
                    pass

            if paused is False or self.end_of_queue is False and self.voice.channel.members != 0:
                # send a message for the music that we are now playing
                try:
                    await self.ctx.send(f"Now playing: {self.current().title}")
                except RuntimeError:
                    pass

            self.voice = voice
            self.end_of_queue = False
        else:
            self.current_pos = 0
