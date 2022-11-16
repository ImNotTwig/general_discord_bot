from math import ceil

import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

from cogs.Unbound import constants

from cogs.Unbound.unbound_data import *

############-UNBOUND COMMANDS-#################################################################################

class UnboundCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-MOVES COMMAND-####################################################################################

    @commands.command(name='moves', case_insensitive=True)             #MOVES
    async def moves(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))
        lvl_up_element = lvlupmoves_dict.get(args ,False)              #querying for the dictionary

        if lvl_up_element is False:                                    #if no dictionary found, jump out of this
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

    @commands.command(name='eggmoves', case_insensitive=True)          #EGGMOVES
    async def eggmoves(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))
        egg_moves_element = eggmoves_dict.get(args, False)             #querying for the dictionary

        if egg_moves_element is False:                                 #if no dictionary found, jump out of this
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

    @commands.command(name='ability', case_insensitive=True)           #ABILITY
    async def ability(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))
        abilities_element = abilities_dict.get(args, False)

        if abilities_element is False:                                 #if no dictionary found return and send error message
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

    @commands.command(name='tmlocation', aliases=['tm'], case_insensitive=True) #TMLOCATION
    async def tmlocation(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))
        q = args

        searchThis = tm_name_number_mapping.get(q, q)                   #checking if the query is present in the mapping
        #can only be possible if query was a number between 1 and 120 (inclusive)
        # obtain name of tm to search here

        tmlocation_element = tmlocation_dict.get(searchThis, False)     #querying using the name now

        if tmlocation_element is False:                                 #if no dictionary found, jump out of this
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

    @commands.command(name='z', case_insensitive=True)                  #Z
    async def z(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        z_element = zlocation_dict.get(args, False)                     #query for z crystal

        if z_element is False:                                          #does entry exist?
            await ctx.send(constants.invalid_text)                      #if not send error
            return

        embedTitle = z_element['name'].title()                          #extract name of z crystal
        embedBody = z_element['location']                               #extract location of z crystal
        embedToSend = discord.Embed(
            title=embedTitle,
            description=embedBody)
        await ctx.send(embed=embedToSend)                               #send embed

############-MEGASTONE COMMAND-################################################################################

    @commands.command(name='megastone', case_insensitive=True)          #MEGASTONE
    async def megastone(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        megastone_element = megastone_dict.get(args, False)             #query for megastone

        if megastone_element is False:                                  #does entry exist?
            await ctx.send(constants.invalid_text)                      #if not send error
            return

        embedTitle = megastone_element['name'].title()                  #extract name of megastone
        embedBody = megastone_element['location']                       #extract location of megastone
        embedToSend = discord.Embed(
            title=embedTitle,
            description=embedBody)
        await ctx.send(embed=embedToSend)                               #send embed

############-HELDITEM COMMAND-################################################################################

    @commands.command(name='helditem', case_insensitive=True)           #HELDITEM
    async def helditem(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        helditem_element = helditem_dict.get(args, False)
        if helditem_element is False:                                   #is key not present, display error message and break out of it
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

    @commands.command(name='location')                                 #LOCATION
    async def location(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        pokelocation_element = pokelocation_dict.get(args, False)
        if pokelocation_element is False:                               #is key not present, display error message and break out of it
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

    @commands.command(name='difficulty', case_insensitive=True)         #DIFFICULTY
    async def difficulty(self, ctx):

        embedToSend = discord.Embed(title= '**Which difficulty should I pick:**')
        for index, (n,v) in enumerate(constants.difficulty_text):       #looping over the command_text list for name and value pairs
            embedToSend.add_field(                                      #adding the fields one at a time
                name=n,
                value=v,
                inline=False)                                           #inline commands not supported on mobile, it lets you have at most 3 columns in your embeds
        await ctx.send(embed=embedToSend)                               #sending the embed
        return

############-SHINY COMMAND-####################################################################################

    @commands.command(name='shiny', aliases=['shinyodd'], case_insensitive=True) #SHINYODD & SHINY
    async def shiny(self, ctx):
        embedTitle = '**Shiny Odds:**'
        embedBody = constants.shiny_odd_text
        embedToSend = discord.Embed(
            title=embedTitle,
            description=embedBody
        )
        await ctx.send(embed=embedToSend)                               #send embed
        return

############-PICKUP COMMAND-###################################################################################

    @commands.command(name='pickup', case_insensitive=True)             #PICKUP
    async def pickup(self, ctx):

        embedToSend = discord.Embed(title=constants.pick_up_image_source[0]) #creates embed
        embedToSend.set_image(url=constants.pick_up_image_source[1])    #adds image to embed
        await ctx.send(embed=embedToSend)                               #send embed
        return

############-KBT COMMAND-######################################################################################

    @commands.command(name='kbt', case_insensitive=True)                #KBT
    async def kbt(self, ctx):

        embedToSend = discord.Embed(title=constants.kbt_image_source[0])#creates embed
        embedToSend.set_image(url=constants.kbt_image_source[1])        #adds image to embed
        await ctx.send(embed=embedToSend)                               #send embed
        return

############-BREEDING COMMAND-#################################################################################

    @commands.command(name='breeding', case_insensitive=True)           #BREEDING
    async def breeding(self, ctx):

        embedToSend = discord.Embed(title= '**Extreme Hyperosmia Breeding Help:**')
        for index, (n,v) in enumerate(constants.breeding_display):      #looping over the command_text list for name and value pairs
            embedToSend.add_field(                                      #adding the fields one at a time
                name=n,
                value=v,
                inline=False)                                           #inline commands not supported on mobile, it lets you have at most 3 columns in your embeds
        await ctx.send(embed=embedToSend)                               #sending the embed
        return

############-CAPS COMMAND-#####################################################################################

    @commands.command(name='caps', aliases=['lvlcaps'], case_insensitive=True) #CAPS & LVLCAPS
    async def caps(self, ctx, *args):
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

    @commands.command(name='download', case_insensitive=True)           #DOWNLOAD
    async def download(self, ctx):

        embedToSend = discord.Embed(
            title='**Pokemon Unbound Official Patch:**',
            description='[Pokemon Unbound Official Patch](https://www.mediafire.com/file/brvvppywnxhmsdb/Pokemon+Unbound+Official+Patch+2.0+.zip/file)'
        )
        await ctx.send(embed=embedToSend)                               #send embed
        return

############-DOCS COMMAND-#####################################################################################

    @commands.command(name='docs', case_insensitive=True)               #DOCS
    async def docs(self, ctx):

        embedTitle = '**Official Unbound Docs:**'                       #extracting the name of the pokemon
        embedBody = "\n".join(
            x for x in
            constants.docs_text)                                        #concatenating the list items

        embedToSend = discord.Embed(
            title=embedTitle,
            description=embedBody)                                      #producing an embed
        await ctx.send(embed=embedToSend)
        return

############-LEARNTM COMMAND-##################################################################################

    @commands.command(name='learntm', case_insensitive=True)            #LEARNTM
    async def learntm(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        tm_element = tm_and_tutor_dict.get(args ,False)                 #querying for the dictionary

        if tm_element is False:                                         #if no dictionary found, jump out of this
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

    @commands.command(name='tutor', case_insensitive=True)              #TUTOR
    async def tutor(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        tutor_element = tm_and_tutor_dict.get(args ,False)              #querying for the dictionary
        if tutor_element is False:                                      #if no dictionary found, jump out of this
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

    @commands.command(name='moveinfo', case_insensitive=True)           #MOVEINFO
    async def moveinfo(self, ctx, *args):
        args = helperfunctions.normalizeString(' '.join(args))

        move_info_element = move_info_dict.get(args ,False)             #querying for the dictionary
        if move_info_element is False:                                  #if no dictionary found, jump out of this
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

    @commands.command(name='stats', case_insensitive=True)              #STATS AND SCALEMONS
    async def stats(self, interaction: discord.interactions, *args):
        scalemonFlag = False                                            #setting the scalemon flag to be false initially

        if len(args) != 0 and helperfunctions.normalizeString(args[0]) == 'scale':
            scalemonFlag = True                                         #setting it to true if user wants scaled stats

        if scalemonFlag:
            args = helperfunctions.normalizeString(' '.join(args[1:]))
        else:
            args = helperfunctions.normalizeString(' '.join(args[0:]))

        base_stat_element = base_stats_dict.get(args, False)            #query dictionary
        if base_stat_element is False:                                  #is key not present, display error message and break out of it
            await interaction.send(content=constants.invalid_text)
            return

        temp = base_stat_element['stats'].copy()

        temp['ability1'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['ability1']), temp['ability1']).get('name', temp['ability1'])
        temp['ability2'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['ability2']), temp['ability2']).get('name', temp['ability2'])
        temp['hiddenAbility'] = ability_desc_dict.get(helperfunctions.normalizeString(temp['hiddenAbility']), temp['hiddenAbility']).get('name', temp['hiddenAbility'])

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

    @commands.command(name='gifts', case_insensitive=True)              #GIFTS
    async def gifts(self, interaction: discord.interactions, *args):
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
