import discord
from discord.ext import commands
import json
from collections import OrderedDict
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from config import config

with open('cogs/Moderation/mute_roles.json', 'r+') as mute_role_file:
    mute_role_dict = json.load(mute_role_file)

with open('cogs/Moderation/server_word_blacklists.json', 'r') as word_blacklists:
    blacklist_dict = json.load(word_blacklists)

with open('cogs/Moderation/unmute_times.json', 'r') as unmute_times:
    unmute_times = json.load(unmute_times)

user_spam_count = OrderedDict()

############-MODERATION COMMANDS-##############################################################################


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-KICK COMMAND-#####################################################################################

    @commands.command(name="kick", pass_context=True, case_insensitive=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.kick(member)
        if reason is not None:
            await ctx.send(f'User {member.mention} has been kicked for {reason}')
            return

        await ctx.send(f'User {member.mention} has been kicked')
        return

############-BAN COMMAND-######################################################################################

    @commands.command(name="ban", pass_context=True, case_insensitive=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.ban(member)
        if reason is not None:
            await ctx.send(f'User {member.mention} has been banned for {reason}')
            return

        await ctx.send(f'User {member.mention} has been banned')
        return

############-MUTE COMMAND-#####################################################################################

    @commands.command(name="mute", pass_context=True, case_insensitive=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *args):
        args = list(args)
        no_time_with_reason = False
        reason = None
        time_units = None
        time_frame = None
        number_list = []
        word_list = []

        if str(ctx.guild.id) not in unmute_times:
            unmute_times[str(ctx.guild.id)] = {}

        if args != []:
            args_list = list(args[0])
            for char in args_list:
                if char.isnumeric():
                    number_list.append(char)
                else:
                    word_list.append(char)
            word_list = ''.join(word_list)

            # find which time frame its in
            match word_list:
                case 'second' | 'sec' | 'seconds' | 'secs' | 's':
                    time_units = ''.join(number_list)
                    multiplier = 1
                    time_frame = "seconds"

                case 'minute' | 'min' | 'minutes' | 'mins' | 'm':
                    time_units = ''.join(number_list)
                    multiplier = 60
                    time_frame = "minutes"

                case 'hour' | 'hours' | 'h':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60
                    time_frame = "hours"

                case 'day' | 'days' | 'd':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24
                    time_frame = "days"

                case 'month' | 'months' | 'M':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30
                    time_frame = "months"

                case 'year' | 'years' | 'y':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12
                    time_frame = "years"

                # ten years
                case 'decade' | 'decades' | 'D':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10
                    time_frame = "decades"

                # hundred years
                case 'centuries' | 'century' | 'C':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10
                    time_frame = "centuries"

                # thousand years
                case 'millenium' | 'milleniums' | 'millenia':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10 * 10
                    time_frame = "millenia"

                # anything under this pretty much doesnt work due to the limitation in dates
                # however its funny to include them

                # million years
                case 'age' | 'ages':
                    time_units = ''.joins(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10 * 10 * 1000
                    time_frame = "ages"

                # ten million years
                case 'epoch' | 'epochs':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10 * 10 * 1000 * 10
                    time_frame = "epochs"

                # hundred million years
                case 'era' | 'eras':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10 * 10 * 1000 * 10 * 10
                    time_frame = "eras"

                # five-hundred million years
                case 'eon' | 'eons':
                    time_units = ''.join(number_list)
                    multiplier = 60 * 60 * 24 * 30 * 12 * 10 * 10 * 10 * 1000 * 10 * 10 * 5
                    time_frame = "eons"

                # assume its a reason and not a time
                case _:
                    no_time_with_reason = True

            if no_time_with_reason is False:
                # check if there is a reason provided
                if time_units == "1" or time_units == 1:
                    if time_frame == "centuries":
                        time_frame = "century"
                    elif time_frame == "millenia":
                        time_frame = "millenium" 
                    else:
                        time_frame = time_frame.removesuffix('s')

                if args[1:] != []:
                    reason = args[1:]

                now = datetime.now()
                then = now + timedelta(seconds=multiplier * int(time_units))

                unmute_times[str(ctx.guild.id)][str(member.id)] = str(then)

                with open('cogs/Moderation/unmute_times.json', 'w') as file:
                    json.dump(unmute_times, file, indent=4)

            # if theres a reason without a time provided
            if no_time_with_reason is True:                    
                reason = args[0:]
        else:
            no_time_with_reason = True

        with open('cogs/Moderation/mute_roles.json', 'r+') as mute_role_file:
            mute_role_dict = json.load(mute_role_file)

        mute_role_name = mute_role_dict[str(ctx.guild.id)]
        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)
        await member.add_roles(mute_role)

        # if reason is an empty list set it to None
        if reason == []:
            reason = None

        # if there is a reason
        if reason is not None:
            # if there is a reason but no time
            if no_time_with_reason is True:
                await ctx.send(f'{member} has been muted for {" ".join(reason)}.')
            # if there is a reason and a time
            else:
                await ctx.send(f'{member} has been muted for {" ".join(reason)} for {time_units} {time_frame}.')
        # if there is no reason
        else:
            # if there is no time
            if no_time_with_reason is True:
                await ctx.send(f'{member} has been muted.')
            # if there is a time but no reason
            else:
                await ctx.send(f'{member} has been muted for {time_units} {time_frame}.')

############-UNMUTE COMMAND-###################################################################################

    @commands.command(name="unmute", pass_context=True, case_insensitive=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):

        mute_role_name = mute_role_dict[str(ctx.guild.id)]

        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)

        await member.remove_roles(mute_role)

        await ctx.send(f'{member} has been un-muted')
        return

############-MUTEROLE COMMAND-#################################################################################

    @commands.command(name="muterole", case_insensitive=True)
    @commands.has_permissions(manage_roles=True)
    async def muterole(self, ctx, role: discord.Role):

        mute_role_dict[str(ctx.guild.id)] = str(role)

        with open('cogs/Moderation/mute_roles.json', 'w') as file:
            json.dump(mute_role_dict, file, indent=4)

        await ctx.send(f'Set mute role to {role}.')
        return

############-UNMUTE DETECTOR-##################################################################################

    @commands.Cog.listener()
    async def on_ready(self):
        print("Starting unmute detector...")
        # check if a person needs to be unmuted according to the timestamp in a file
        while True:
            await asyncio.sleep(.1)
            for (k, v) in unmute_times.items():
                for (member, time) in v.items():
                    if pd.to_datetime(time) < pd.to_datetime(str(datetime.now())):
                        server = self.bot.get_guild(int(k))
                        mute_role_name = mute_role_dict[str(server.id)]
                        mute_role = discord.utils.get(server.roles, name=mute_role_name)
                        user = server.get_member(int(member))
                        await user.remove_roles(mute_role)

                        user = self.bot.get_user(int(member))

                        await user.send("You have been unmuted in {}.".format(server.name))
                        del unmute_times[str(k)][member]
                        with open('cogs/Moderation/unmute_times.json', 'w') as file:
                            json.dump(unmute_times, file, indent=4)

############-PURGE COMMAND-####################################################################################

    @commands.command(name="purge", case_insensitive=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, arg: int):
        await ctx.channel.purge(limit=arg + 1)

############-BLACKLIST COMMAND-################################################################################

    @commands.command(name="blacklist", aliases=["bl"], case_insensitive=True)
    @commands.has_permissions(manage_messages=True)
    async def blacklist(self, ctx, arg: str):
        if ctx.guild.id not in blacklist_dict.keys():
            blacklist_dict[ctx.guild.id] = []

        blacklist_dict[ctx.guild.id].append(arg)

        with open('cogs/Moderation/server_word_blacklists.json', 'w') as file:
            json.dump(blacklist_dict, file, indent=4)

        await ctx.channel.send(f"Added {arg} to blacklist!")

############-ANTISPAM AND BLACKLIST-###########################################################################

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.guild.id not in blacklist_dict.keys():
            blacklist_dict[message.guild.id] = []

        #if author is an administrator
        if message.author.guild_permissions.administrator is True:
            return

        author_id = str(message.author.id)
        words_in_message = message.content.split()

        #if message has a blacklisted word
        for black_listed_word in blacklist_dict[message.guild.id]:
            for word in words_in_message:
                if word in black_listed_word:
                    await message.delete()
                    await message.channel.send(f'{message.author.mention} your message contains a blacklisted word, it has been deleted.')

        #if author has the manage messages permission
        if message.author.guild_permissions.manage_messages:
            return
        #if the author is a bot
        if message.author.bot:
            return

        #if the antispam feature is turned on
        if config.spam_settings.antispam:
            if author_id not in user_spam_count.keys():
                #if the user's id is not in the dictionary add it
                user_spam_count[author_id] = [0, message.content]

            if user_spam_count[author_id][1] != message.content:
                #if the message in the user's spam count is not the same reset the counter
                user_spam_count[author_id] = [0, message.content]

            if user_spam_count[author_id][0] == 0:
                #if the spam count is 0 set it to 1
                user_spam_count[author_id][0] = 1

            elif user_spam_count[author_id][0] == config.spam_settings.spam_count - 1:
                #if the user has sent the same message the amount of times in a row
                #that is defined by the config they will be muted
                mute_role_name = mute_role_dict[author_id]
                mute_role = discord.utils.get(message.guild.roles, name=mute_role_name)

                await message.author.add_roles(mute_role)
                await message.channel.send(f"{message.author.mention} has been muted for spamming.")
                user_spam_count[author_id][0] = 0

            else:
                #add to the counter
                user_spam_count[author_id][0] += 1

            if len(user_spam_count) > 50:
                user_spam_count.pop(50)

###############################################################################################################
