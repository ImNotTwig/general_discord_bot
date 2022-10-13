import discord
from discord.ext import commands
import json

with open('cogs/Moderation/mute_roles.json', 'r+') as file:
    mute_role_dict = json.load(file)

############-MODERATION COMMANDS-##############################################################################

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-KICK COMMAND-#####################################################################################

    @commands.command(name="kick", pass_context = True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.kick(member)
        if reason != None:
            await ctx.send(f'User {member.mention} has been kicked for {reason}')
            return

        await ctx.send(f'User {member.mention} has been kicked')
        return

############-BAN COMMAND-######################################################################################

    @commands.command(name="ban", pass_context = True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.ban(member)
        if reason != None:
            await ctx.send(f'User {member.mention} has been banned for {reason}')
            return

        await ctx.send(f'User {member.mention} has been banned')
        return

############-MUTE COMMAND_#####################################################################################

    @commands.command(name="mute", pass_context=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):

        mute_role_name = mute_role_dict[str(ctx.guild.id)]

        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)

        await member.add_roles(mute_role)

        if reason != None:
            await ctx.send(f'{member} has been muted for {reason}')
            return

        await ctx.send(f'{member} has been muted')
        return

############-UNMUTE COMMAND_###################################################################################

    @commands.command(name="unmute", pass_context=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):

        mute_role_name = mute_role_dict[str(ctx.guild.id)]

        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)

        await member.remove_roles(mute_role)

        await ctx.send(f'{member} has been un-muted')
        return

############-MUTEROLE COMMAND_#################################################################################

    @commands.command(name='muterole')
    @commands.has_permissions(manage_roles=True)
    async def muterole(self, ctx, role: discord.Role):

        if ctx.guild.id not in mute_role_dict.keys():
            mute_role_dict[ctx.guild.id] = str(role)

        with open('cogs/Moderation/mute_roles.json', 'r+') as file:
            json.dump(mute_role_dict, file, indent=4)

        await ctx.send(f'set mute role to {role}')
        return
