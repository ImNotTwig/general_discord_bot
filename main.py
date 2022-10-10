import discord
import numpy as np
from dotenv import load_dotenv
from discord.ext import commands
import os
import asyncio
import youtube_dl
import requests
from lyricsgenius import Genius
import json
from math import ceil
from reactionmenu import ViewButton, ViewMenu

import constants
import helperfunctions
import utilities

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='~', intents=intents, help_command=None)
genius = Genius(access_token=os.getenv('GENIUS_TOKEN'), remove_section_headers=True)

############-IMPORTING UNBOUND DATA JSONS TO DICTIONARIES-#####################################################

with open("DATA/abilities.json", encoding='utf8') as file:
    abilities_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/ability_description.json", encoding='utf8') as file:
    ability_desc_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/eggmoves.json", encoding='utf8') as file:
    eggmoves_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/helditem.json", encoding='utf8') as file:
    helditem_dict = helperfunctions.listToDict('itemname',  json.load(file))

with open("DATA/Learnsets.json", encoding='utf8') as file:
    lvlupmoves_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/megastone.json", encoding='utf8') as file:
    megastone_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/pokelocation.json", encoding='utf8') as file:
    pokelocation_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/scalemon.json", encoding='utf8') as file:
    scalemon_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/tmlocation.json", encoding='utf8') as file:
    tmlocation_dict = helperfunctions.listToDict('tmname',  json.load(file))
    tm_name_number_mapping = dict(zip(np.char.mod('%d', np.arange(1, 121, 1)), tmlocation_dict.keys())) #making a number string mapping for the tm dictionary

with open("DATA/tm_and_tutor.json", encoding='utf8') as file:
    tm_and_tutor_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/zlocation.json", encoding='utf8') as file:
    zlocation_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/movedescription.json", encoding='utf8') as file:
    move_info_dict = helperfunctions.listToDict('movename',  json.load(file))

with open("DATA/Base_Stats.json", encoding='utf8') as file:
    base_stats_dict = helperfunctions.listToDict('name',  json.load(file))

with open("DATA/gifts.json", encoding='utf8') as file:
    gifts_dict = json.load(file)

###############################################################################################################

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
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

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


def prepare_continue_queue(ctx):
    fut = asyncio.run_coroutine_threadsafe(continue_queue(ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)


async def continue_queue(ctx):
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
    # Finds author's session.
    session = check_session(ctx)

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=session.guild)

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
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return

############-QUEUE COMMAND-####################################################################################

@bot.command(name='queue', aliases=['q'])
async def queue(ctx):
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

@bot.command(name="remove")
async def remove(ctx, *args):
    session = check_session(ctx)
    queue = session.q.queue

    if len(queue) == 0:
        return
    arg = int(args[0]) - 1

    await ctx.send(f"removed {queue[arg][0]} from the queue")
    queue.pop(arg)
    return

############-LEAVE COMMAND-####################################################################################

@bot.command(name='leave', aliases=["quit", "fuckoff", "disconnect"])
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected:
        check_session(ctx).q.clear_queue()
        await voice.disconnect()
    else:
        await ctx.send("The bot is not connected")

############-PAUSE COMMAND-####################################################################################

@bot.command(name='pause')
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("I am not playing anything")

############-RESUME COMMAND-###################################################################################

@bot.command(name='resume')
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused:
        voice.resume()
    else:
        await ctx.send("Music is not paused")

############-STOP COMMAND-#####################################################################################

@bot.command(name='stop')
async def stop(ctx):
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

###############################################################################################################

############-UNBOUND COMMANDS-#################################################################################

############-MOVES COMMAND-####################################################################################

@bot.command(name='moves')                                         #MOVES
async def moves(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))
    lvl_up_element = lvlupmoves_dict.get(args ,False)              #querying for the dictionary

    if lvl_up_element == False:                                    #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                     #error message
        return
    embedTitle = lvl_up_element['name'].title()                    #setting name

    embedBody = '\n'.join(
        ' - '.join(str(y).title() for y in x)
        for x in lvl_up_element['lvlUpMoves'])                     #same as the for loop above OR the one liner above

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                              #sending the embed

############-EGGMOVES COMMAND-#################################################################################

@bot.command(name='eggmoves')                                      #EGGMOVES
async def eggmoves(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))
    egg_moves_element = eggmoves_dict.get(args, False)             #querying for the dictionary

    if egg_moves_element == False:                                 #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                     #error message
        return
    embedTitle = egg_moves_element['name'].title()                 #extracting the name of the pokemon
    embedBody = "\n".join(
        x.lower() for x in
        egg_moves_element['eggMoves'])                             #concatenating the list items
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)                                     #producing an embed
    await ctx.send(embed=embedToSend)                              #sending the embed

############-ABILITY COMMAND-##################################################################################

@bot.command(name='ability')                                       #ABILITY
async def ability(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))
    abilities_element = abilities_dict.get(args, False)

    if abilities_element == False:                                 #if no dictionary found return and send error message
        await ctx.send(constants.invalid_text)                     #error
        return

    ability1, ability2, hiddenAbility = [str(x).lower().title()    #extracting abilities and ability descriptions for embedText
                                         for x in abilities_element['Ability']]

    ability1_desc, ability2_desc, hidden_ability_desc = [ability_desc_dict[helperfunctions.normalizeString(x)]['effect']
                                                         for x in (ability1, ability2, hiddenAbility)]

    embedText = helperfunctions.StringFormatter(
        constants.ability_display,
        str(ability1),
        ability1_desc,
        str(ability2),
        ability2_desc,
        str(hiddenAbility),
        hidden_ability_desc)

    embedTitle = abilities_element['name'].title()                  # extract name of pokemon
    embedBody = "\n" + embedText
    embedToSend = discord.Embed(                                    #producing an embed
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #sending the embed

############-TMLOCATION COMMAND-###############################################################################

@bot.command(name='tmlocation', aliases=['tm'])                     #TMLOCATION
async def tmlocation(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))
    q = args

    searchThis = tm_name_number_mapping.get(q, q)                   #checking if the query is present in the mapping
                                                                    #can only be possible if query was a number between 1 and 120 (inclusive)
                                                                    # obtain name of tm to search here

    tmlocation_element = tmlocation_dict.get(searchThis, False)     #querying using the name now

    if tmlocation_element == False:                                 #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                      #error message
        return

    embedTitle = "TM# "+str(tmlocation_element['tmnumber'])         #extracting the name of the pokemon
    embedBody = f'''{tmlocation_element['tmname'].title()}
    {tmlocation_element['tmlocation']}'''                           #tm name + tm location in body
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)                                      #producing an embed
    await ctx.send(embed=embedToSend)                               #sending the embed

############-Z COMMAND-########################################################################################

@bot.command(name='z')                                              #Z
async def z(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    z_element = zlocation_dict.get(args, False)                     #query for z crystal

    if z_element == False:                                          #does entry exist?
        await ctx.send(constants.invalid_text)                      #if not send error
        return

    embedTitle = z_element['name'].title()                          #extract name of z crystal
    embedBody = z_element['location']                               #extract location of z crystal
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #send embed

############-MEGASTONE COMMAND-################################################################################

@bot.command(name='megastone')                                      #MEGASTONE
async def megastone(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    megastone_element = megastone_dict.get(args, False)             #query for megastone

    if megastone_element == False:                                  #does entry exist?
        await ctx.send(constants.invalid_text)                      #if not send error
        return

    embedTitle = megastone_element['name'].title()                  #extract name of megastone
    embedBody = megastone_element['location']                       #extract location of megastone
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #send embed

############-HELDITEM COMMAND-################################################################################

@bot.command(name='helditem')                                       #HELDITEM
async def helditem(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    helditem_element = helditem_dict.get(args, False)
    if helditem_element == False:                                   #is key not present, display error message and break out of it
        await ctx.send(constants.invalid_text +
                       " What you are looking for might not be an item that can be obtained from wild pokemons")
        return

    embedTitle = helditem_element['itemname'].title()               #extract name of item
    embedBody = helditem_element['location']                        #extract location of item
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-LOCATION COMMAND-#################################################################################

@bot.command(name='location')                                       #LOCATION
async def location(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    pokelocation_element = pokelocation_dict.get(args, False)
    if pokelocation_element == False:                               #is key not present, display error message and break out of it
        await ctx.send(constants.invalid_text)
        return

    embedTitle = pokelocation_element['name'].title()               #extract name of pokemon
    embedBody = pokelocation_element['location']                    #extract location of pokemon
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-DIFFICULTY COMMAND-###############################################################################

@bot.command(name='difficulty')                                     #DIFFICULTY
async def difficulty(ctx):

    embedToSend = discord.Embed(title= '**Which difficulty should I pick:**')
    for index, (n,v) in enumerate(constants.difficulty_text):       #looping over the command_text list for name and value pairs
        embedToSend.add_field(                                      #adding the fields one at a time
            name=n,
            value=v,
            inline=False)                                           #inline commands not supported on mobile, it lets you have at most 3 columns in your embeds
    await ctx.send(embed=embedToSend)                               #sending the embed
    return

############-SHINY COMMAND-####################################################################################

@bot.command(name='shiny', aliases=['shinyodd'])                    #SHINYODD & SHINY
async def shiny(ctx):
    embedTitle = '**Shiny Odds:**'
    embedBody = constants.shiny_odd_text
    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody
    )
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-PICKUP COMMAND-###################################################################################

@bot.command(name='pickup')                                         #PICKUP
async def pickup(ctx):

    embedToSend = discord.Embed(title=constants.pick_up_image_source[0]) #creates embed
    embedToSend.set_image(url=constants.pick_up_image_source[1])    #adds image to embed
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-KBT COMMAND-######################################################################################

@bot.command(name='kbt')                                            #KBT
async def kbt(ctx):

    embedToSend = discord.Embed(title=constants.kbt_image_source[0])#creates embed
    embedToSend.set_image(url=constants.kbt_image_source[1])        #adds image to embed
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-BREEDING COMMAND-#################################################################################

@bot.command(name='breeding')                                       #BREEDING
async def breeding(ctx):

    embedToSend = discord.Embed(title= '**Extreme Hyperosmia Breeding Help:**')
    for index, (n,v) in enumerate(constants.breeding_display):      #looping over the command_text list for name and value pairs
        embedToSend.add_field(                                      #adding the fields one at a time
            name=n,
            value=v,
            inline=False)                                           #inline commands not supported on mobile, it lets you have at most 3 columns in your embeds
    await ctx.send(embed=embedToSend)                               #sending the embed
    return

############-CAPS COMMAND-#####################################################################################

@bot.command(name='caps', aliases=['lvlcaps'])                      #CAPS & LVLCAPS
async def caps(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    if args == 'vanilla' or args == 'v':
        embedBody = constants.caps_template.format(*constants.vanilla_caps)
        embedTitle = '**Level Caps: Vanilla**'
    else:
        embedBody = constants.caps_template.format(*constants.other_caps)
        embedTitle = '**Level Caps: Difficult+**'

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody
    )
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-DOWNLOAD COMMAND-#################################################################################

@bot.command(name='download')                                       #DOWNLOAD
async def download(ctx):

    embedToSend = discord.Embed(
        title='**Pokemon Unbound Official Patch:**',
        description='[Pokemon Unbound Official Patch](https://www.mediafire.com/file/brvvppywnxhmsdb/Pokemon+Unbound+Official+Patch+2.0+.zip/file)'
    )
    await ctx.send(embed=embedToSend)                               #send embed
    return

############-DOCS COMMAND-#####################################################################################

@bot.command(name='docs')                                           #DOCS
async def docs(ctx):

    embedTitle = '**Official Unbound Docs:**'                        #extracting the name of the pokemon
    embedBody = "\n".join(
        x for x in
        constants.docs_text)                                        #concatenating the list items

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)                                      #producing an embed
    await ctx.send(embed=embedToSend)
    return

############-LEARNTM COMMAND-##################################################################################

@bot.command(name='learntm')                                        #LEARNTM
async def learntm(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    tm_element = tm_and_tutor_dict.get(args ,False)                 #querying for the dictionary

    if tm_element == False:                                         #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                      #error message
        return
    embedTitle = "TM's compatible with "
    embedBody = ", ".join(
        x.title() for x in
        tm_element.get('tmMoves', "")
    )
    embedTitle += tm_element['name'].title()                        #extracting the name of the pokemon

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)                                      #producing an embed
    await ctx.send(embed=embedToSend)                               #sending the embed
    return

############-TUTOR COMMAND-####################################################################################

@bot.command(name='tutor')                                          #TUTOR
async def tutor(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    tutor_element = tm_and_tutor_dict.get(args ,False)              #querying for the dictionary
    if tutor_element == False:                                      #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                      #error message
        return
    embedTitle = "Tutor moves learnt by "
    embedBody = ", ".join(
        x.title() for x in
        tutor_element.get('tutorMoves', "")
    )
    embedTitle += tutor_element['name'].title()                     #extracting the name of the pokemon

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)                                      #producing an embed
    await ctx.send(embed=embedToSend)                               #sending the embed
    return

############-MOVEINFO COMMAND-#################################################################################

@bot.command(name='moveinfo')                                       #MOVEINFO
async def moveinfo(ctx, *args):
    args = helperfunctions.normalizeString(' '.join(args))

    move_info_element = move_info_dict.get(args ,False)             #querying for the dictionary
    if move_info_element == False:                                  #if no dictionary found, jump out of this
        await ctx.send(constants.invalid_text)                      #error message
        return
    embedTitle = move_info_element['movename'].title()              #setting name

    embedBody = constants.move_info_display.format(
        *[*(move_info_element.values())][1:])                       #removing the first element, it's the name being displayed in the title

    embedToSend = discord.Embed(
        title=embedTitle,
        description=embedBody)
    await ctx.send(embed=embedToSend)                               #sending the embed
    return

############-STATS COMMAND-####################################################################################

@bot.command(name='stats')                                          #STATS AND SCALEMONS
async def stats(interaction: discord.interactions, *args ):
    scalemonFlag = False                                            #setting the scalemon flag to be false initially

    if len(args) != 0 and helperfunctions.normalizeString(args[0]) == 'scale':
        scalemonFlag = True                                         #setting it to true if user wants scaled stats

    if scalemonFlag:
        args = helperfunctions.normalizeString(' '.join(args[1:]))
    else:
        args = helperfunctions.normalizeString(' '.join(args[0:]))

    base_stat_element = base_stats_dict.get(args, False)            #query dictionary
    if base_stat_element == False:                                  #is key not present, display error message and break out of it
        await interaction.send(content = constants.invalid_text)
        return

    temp = base_stat_element['stats'].copy()

    temp['ability1'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['ability1']),  temp['ability1']).get('name', temp['ability1'])
    temp['ability2'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['ability2']),  temp['ability2']).get('name', temp['ability2'])
    temp['hiddenAbility'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['hiddenAbility']),  temp['hiddenAbility']).get('name', temp['hiddenAbility'])

    s, t, c, e, i, b, a, ch = helperfunctions.getComplexStats(temp, scalemonFlag)

    stat_menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed, remove_buttons_on_timeout=True, all_can_click=False)

    if scalemonFlag:
        simple_page = discord.Embed(title="Scalemon " + base_stat_element['name'].title())
        simple_page.set_footer(text=constants.scalemon_warning)
        complex_page = discord.Embed(title="Scalemon " + base_stat_element['name'].title())
        complex_page.set_footer(text=constants.scalemon_warning)

    else:
        simple_page = discord.Embed(title=base_stat_element['name'].title())
        complex_page = discord.Embed(title=base_stat_element['name'].title())

    simple_page = helperfunctions.addFieldToEmbeds(simple_page, [t, s, a], ["Type", "Stats", "Abilities"])
    complex_page = helperfunctions.addFieldToEmbeds(complex_page, [b, i, e, c, ch], [
        "Breeding Information",
        "Items",
        "EV Yields",
        "Catch Information",
        "Miscellaneous"])

    stat_menu.add_page(simple_page)
    stat_menu.add_page(complex_page)

    stat_menu.add_button(ViewButton.next())

    await stat_menu.start() #posting the menu
    return

############-GIFTS COMMAND-####################################################################################

@bot.command(name='gifts')                                          #GIFTS
async def gifts(interaction: discord.interactions, *args):
    menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed, remove_buttons_on_timeout=True, all_can_click=False)

    args = helperfunctions.normalizeString(' '.join(args))
    if args == 'bfd':                                               #If user asked for BFD, we set the search_key to be bfd, unless display maingame gifts
        search_key = 'bfd'
    else:
        search_key = 'maingame'

    numOfPagesGifts = ceil(len(gifts_dict[search_key]) / constants.maxEntriesPerPageGifts)

    pages = []

    for i in range(0, numOfPagesGifts):                              #Producing the pages
        pages.append(discord.Embed(title=f"Gift Page #{i+1}"))

        for j in range(0, constants.maxEntriesPerPageGifts):         #adding information to the pages
            currentIndex = j + i * constants.maxEntriesPerPageGifts
            if currentIndex == len(gifts_dict[search_key]):
                break
            pages[i].add_field(
                name=gifts_dict[search_key][currentIndex][1],        #pokemon name
                value=f'`{gifts_dict[search_key][currentIndex][0]}`', #gift code
                inline=False
            )

    for p in pages:                                                  #adding the pages to the menu
        menu.add_page(p)

    menu.add_button(ViewButton.back())
    menu.add_button(ViewButton.next())

    await menu.start()                                               #sending the embed
    return

###############################################################################################################

###############################################################################################################

###############################################################################################################

bot.run(os.getenv('TOKEN'))

