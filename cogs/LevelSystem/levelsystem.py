import discord
from discord.ext import commands
import json
from dataclasses import dataclass
from dataclasses_serialization.json import JSONSerializer
import asyncio

with open('config.json', 'r+') as file:
    config = json.load(file)
with open('cogs/LevelSystem/levels.json', 'r+') as file:
    levels = json.load(file)

@dataclass
class UserXp:
    level: int
    total_xp: int
    current_xp: int
    xp_needed: int
    can_gain_xp: bool

#xp_needed formula is:
# 5*(level^2) + (50*level) + 100 - current_xp
#when xp_needed reaches 0 increase level by 1 and calculate new xp_needed

############-LEVELSYSTEM COMMANDS-#############################################################################

class LevelSystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-XP COMMAND-#######################################################################################

    @commands.command(name="xp", pass_context=True)
    async def xp(self, ctx):
        #setting author name
        author = ctx.message.author.name + '#' + ctx.message.author.discriminator
        #if author is in the levels dict already
        if author in levels.keys():
            #sending the embed
            embed_to_send = discord.Embed(
                description=f'{author} is level {levels[author]["level"]}'
            )
            await ctx.send(embed=embed_to_send)
        #if the author is *not* in the levels dict already
        else:
            #create a new UserXp dataclass with level 0
            levels[author] = UserXp(0, 0, 0, 100, True)
            #sending the embed
            embed_to_send = discord.Embed(
                description=f'{author} is level {levels[author]["level"]}'
            )
            await ctx.send(embed=embed_to_send)
        #writing the new dictionary to the levels.json file
        with open('cogs/LevelSystem/levels.json', 'r+') as file:
            json.dump(JSONSerializer.serialize(levels), file, indent=4)
    
############-DETECT MESSAGE FOR XP-############################################################################
    
    @commands.Cog.listener()
    async def on_message(self, message):
    
        author_name = message.author.name + '#' + message.author.discriminator
        
        
        if message.author.bot is True:
            return
        
        if author_name in levels.keys():
            if levels[author_name]['can_gain_xp'] is True:
                levels[author_name]['current_xp'] += config['level_system']['xp_per_message']
                levels[author_name]['total_xp'] += config['level_system']['xp_per_message']
                levels[author_name]['xp_needed'] -= config['level_system']['xp_per_message']
                
                with open('cogs/LevelSystem/levels.json', 'r+') as file:
                    json.dump(JSONSerializer.serialize(levels), file, indent=4)

                levels[author_name]['can_gain_xp'] = False
                await asyncio.sleep(config['level_system']['cooldown_in_seconds'])
                levels[author_name]['can_gain_xp'] = True
                