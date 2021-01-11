# mkwiimmfi_status v1.0.1
# A Discord Bot (using the discord.py python library) that shows the current amount of people playing Mario Kart Wii
# on the custom Wiimmfi servers.
# Wiimmfi server website (from which the data is taken from): https://wiimmfi.de/stat?m=88

import pandas as pd
import discord
from discord.ext import commands, tasks

URL = "https://wiimmfi.de/stat?m=80"
TOKEN = open("token.txt", "r").readline()
client = commands.Bot(command_prefix='mkw:')


# answers with the ms latency
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms ')


# We delete default help command
client.remove_command('help')


# Embedded help with list and details of commands
@client.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(
        colour=discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='mkw:status', value='Shows how many players are online, and in which game regions', inline=False)
    embed.add_field(name='mkw:help', value='Returns this help list', inline=False)
    embed.add_field(name='mkw:ping', value='Returns bot respond time in milliseconds', inline=False)
    embed.add_field(name="Website the data is from:", value=" https://wiimmfi.de/stat?m=88", inline=False)
    await ctx.send(embed=embed)


# returns the table of the number of players online from https://wiimmfi.de/stat?m=88, ordered by the number of players
def get_sorted_table():
    table = pd.read_html(io=URL, match="Mario Kart Wii: Regions")[0]
    return table.sort_values(by=('Mario Kart Wii: Regions', 'Value'))


# returns the number of players online, in each game region
@client.command()
async def status(ctx):
    table = get_sorted_table()
    embed = discord.Embed(
        colour=discord.Colour.green())
    embed.set_author(name="Mario Kart Wii: Wiimmfi Online players")
    for index, row in table.iterrows():
        embed.add_field(name=row[0], value=row[1], inline=False)
    await ctx.send(embed=embed)


@tasks.loop(minutes=2)
async def bot_activity():
    table = get_sorted_table()
    players_count = table.tail(1).iat[0, 1]
    activity = discord.Activity(name='%d people playing Mario Kart Wii online.' % players_count,
                                type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)


@client.event
async def on_ready():
    bot_activity.start()


# If there is an error, it will answer with an error
@client.event
async def on_command_error(ctx, error):
    # emoji = '\N{EYES}'
    # await ctx.add_reaction(emoji)
    await ctx.send(f'Error. Try !help ({error})')


client.run(TOKEN)
