import discord
from discord.ext import commands
import json
import asyncio

with open('config.json', 'r+') as file:
    config = json.load(file)
with open('cogs/LevelSystem/levels.json', 'r+') as file:
    levels = json.load(file)
with open('cogs/LevelSystem/server_level_system_enabler.json', 'r+') as file:
    server_enabler = json.load(file)

# since sometimes members data will have false it will be written to file
# this sets it to true when it loads the file so users can gain xp
for server in levels:
    for member in levels[server]:
        levels[server][member]['can_gain_xp'] = True

# xp_needed formula is:
# 5*(level^2) + (50*level) + 100 - current_xp

############-LEVELSYSTEM COMMANDS-#############################################################################

class LevelSystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-XP COMMAND-#######################################################################################

    @commands.command(name="xp", pass_context=True)
    async def xp(self, ctx):
        # setting author name
        server = str(ctx.message.guild.id)
        author = ctx.author.name + '#' + ctx.author.discriminator
        # if author is in the levels dict already
        if server in levels.keys():
            if author in levels[server]:
                # sending the embed

                embed = discord.Embed(title=f"{ctx.author.name}'s level stats")
                embed.add_field(name="Name", value=ctx.author.mention, inline=True)
                embed.add_field(name="Xp", value=levels[server][author]['current_xp'], inline=True)
                embed.add_field(name="Level", value=levels[server][author]['level'], inline=True)
                
                current_xp = levels[server][author]['current_xp']
                xp_needed = levels[server][author]['xp_needed']
                xp_needed_to_lvl_up = xp_needed - current_xp
                
                amount_per_box = xp_needed / 20                
                current_boxes = current_xp / amount_per_box
                boxes_left = xp_needed_to_lvl_up / amount_per_box

                embed.add_field(name="Progress Bar [level]", value=(int(current_boxes)) * ":blue_square:" + (int(boxes_left)) * ":white_large_square:", inline=False)
                embed.set_thumbnail(url=ctx.author.avatar.url)
                
                await ctx.send(embed=embed)
        # if the author is *not* in the levels dict already
        else:
            levels[server] = {}
            # create new user data
            levels[server][author]['level'] = 0
            levels[server][author]['total_xp'] = 0
            levels[server][author]['current_xp'] = 0
            levels[server][author]['xp_needed'] = 100
            levels[server][author]['can_gain_xp'] = True
            # sending the embed
            
            embed = discord.Embed(title=f"{ctx.author.name}'s level stats")
            embed.add_field(name="Name", value=ctx.author.mention, inline=True)
            embed.add_field(name="Xp", value=levels[server][author]['current_xp'], inline=True)
            embed.add_field(name="Level", value=levels[server][author]['level'], inline=True)
            
            current_xp = levels[server][author]['current_xp']
            xp_needed = levels[server][author]['xp_needed']
            xp_needed_to_lvl_up = xp_needed - current_xp

            amount_per_box = xp_needed / 20
            current_boxes = current_xp / amount_per_box
            boxes_left = xp_needed_to_lvl_up / amount_per_box
                            
            embed.add_field(name="Progress Bar [level]", value=(int(current_boxes)) * ":blue_square:" + (int(boxes_left)) * ":white_large_square:", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

############-DETECT MESSAGE FOR XP-############################################################################

    @commands.Cog.listener()
    async def on_message(self, message):
        # if the server isnt in the server_enabler dict
        if str(message.guild.id) not in server_enabler.keys():
            server_enabler[str(message.guild.id)] = False
            with open('cogs/LevelSystem/server_level_system_enabler.json', 'r+') as file:
                json.dump(server_enabler, file, indent=4)
        
        # if the server has the level system turned on 
        if server_enabler[str(message.guild.id)] is True:

            server = str(message.guild.id)
            author_name = message.author.name + '#' + message.author.discriminator

            # if author is a bot
            if message.author.bot is True:
                return
            
            # if the server isnt in the levels dict yet, add it
            if server not in levels.keys():    
                levels[server] = {}
                # create a new UserXp dataclass with level 0
                levels[server][author_name]['level'] = 0
                levels[server][author_name]['total_xp'] = 0
                levels[server][author_name]['current_xp'] = 0
                levels[server][author_name]['xp_needed'] = 100
                levels[server][author_name]['can_gain_xp'] = True
                          
            # if the author can gain xp
            if levels[server][author_name]['can_gain_xp'] is True:
                # increase authors total_xp and current_xp
                levels[server][author_name]['current_xp'] += config['level_system']['xp_per_message']
                levels[server][author_name]['total_xp'] += config['level_system']['xp_per_message']
            
                # if the current_xp is over or equal to the xp_needed 
                if levels[server][author_name]['current_xp'] >= levels[server][author_name]['xp_needed']:
                    # calculate how much current_xp went over xp_needed if it did
                    if levels[server][author_name]['current_xp'] > levels[server][author_name]['xp_needed']:
                        #set the authors current_xp to the difference between it and the xp_needed
                        levels[server][author_name]['current_xp'] = levels[server][author_name]['current_xp'] - levels[server][author_name]['xp_needed']

                    # increment the authors level by 1    
                    levels[server][author_name]['level'] += 1
                    #setting the new xp_needed according to the formula defined at the top of this file
                    levels[server][author_name]['xp_needed'] = 5 * (levels[server][author_name]['level'] ^ 2) + (50 * levels[server][author_name]['level']) + 100
                
                # write the new xp amounts to levels.json
                with open('cogs/LevelSystem/levels.json', 'r+') as file:
                    json.dump(levels, file, indent=4)

                # because the file gets written before the
                # can_gain_xp state changes it will never be false in the file

                # don't let the author gain xp until the cooldown is over
                levels[server][author_name]['can_gain_xp'] = False
                await asyncio.sleep(config['level_system']['cooldown_in_seconds'])
                levels[server][author_name]['can_gain_xp'] = True
        # if the server has the level system turned off
        else:
            return    
            
###############################################################################################################

