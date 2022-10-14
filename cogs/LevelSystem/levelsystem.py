import discord
from discord.ext import commands
import json
from dataclasses import dataclass
from dataclasses_serialization.json import JSONSerializer

with open('config.json', 'r+') as file:
    config = json.load(file)
with open('cogs/LevelSystem/levels.json', 'r+') as file:
    levels = json.load(file)

#'twig#3660' {
#    'level': 0,
#    'total_xp': 0,
#    'current_xp': 0
#    'xp_needed': 100
#}

@dataclass
class UserXp:
    level: int
    total_xp: int
    current_xp: int
    xp_needed: int

#xp_needed formula is:
# 5*(level^2) + (50*level) + 100 - current_xp
#when xp_needed reaches 0 increase level by 1 and calculate new xp_needed

############-LEVELSYSTEM COMMANDS-#############################################################################

class LevelSystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="xp", pass_context=True)
    async def xp(self, ctx):
        author = ctx.message.author.name + '#' + ctx.message.author.discriminator

        if author in levels.keys():
            embed_to_send = discord.Embed(
                description=f'{author} is level {levels[author]["level"]}'
            )
            await ctx.send(embed=embed_to_send)
            
        else:
            levels[author] = UserXp(0, 0, 0, 100)
            embed_to_send = discord.Embed(
                description=f'{author} is level {levels[author]["level"]}'
            )
            await ctx.send(embed=embed_to_send)
            
        with open('cogs/LevelSystem/levels.json', 'r+') as file:
            json.dump(JSONSerializer.serialize(levels), file, indent=4)