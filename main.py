""" MKW Wiimmfi Status Bot
A Discord Bot (using the discord.py python library) that shows the current amount of people playing Mario Kart Wii
on the custom Wiimmfi servers.
Wiimmfi server website (from which the data is taken from): https://wiimmfi.de/stat?m=88
"""

import discord
from discord.ext import commands, tasks
import pandas as pd
import json

TOKEN = open("token.txt", "r").readline()
CLIENT_ID = open("client_id.txt", "r").readline()
PREFIX = "mkw:"

STATUS_URL = "https://wiimmfi.de/stat?m=80"
REGIONS_URL = "https://wiimmfi.de/reg-list"
NOTIFICATION_SUBSCRIBERS_JSON = "notification_subscribers.json"

player_count_dict = {}

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
client = commands.Bot(command_prefix=PREFIX, intents=intents)


@client.command()
async def ping(ctx):
    """Returns the bot's latency in milliseconds."""
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms ')


client.remove_command('help')


@client.command(pass_context=True)
async def help(ctx):
    """Help command that returns an embedded list and details of commands, and some additional information."""
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='mkw:status', value='Shows how many players are online, and in which game regions.',
                    inline=False)
    embed.add_field(name='mkw:region "MANY WORDS" or mkw:region WORD',
                    value="Search regions ID's by giving one or several words\nExample: mkw:region \"Mario Kart Fusion\" or mkw:region fun", inline=False)
    embed.add_field(name='mkw:sub REGION_ID or mkw:sub channel REGION_ID',
                    value='Subscribe yourself to receive DM or the current channel (if you own the Manage Channels rights) to be notified to regions events.\nExample: mkw:sub 870 or mkw:sub channel 870', inline=False)
    embed.add_field(name='mkw:unsub REGION_ID|all or mkw:unsub REGION_ID|all',
                    value='Unsubcribe yourself or the current channel (if you own the Manage Channels rights) to regions events notifications.\n'
                          'Example: mkw:unsub all or mkw:unsub 870 or mkw:unsub channel all or mkw:unsub channel 870', inline=False)
    embed.add_field(name='mkw:subs or mkw:subs channel', value='Returns the region list for which you or the current channel (if you own the Manage Channels rights) are subscribed to.', inline=False)
    embed.add_field(name='mkw:invite', value='Returns a link to invite the bot in your server.', inline=False)
    embed.add_field(name='mkw:help', value='Returns this help list.', inline=False)
    embed.add_field(name='mkw:ping', value='Returns bot response time in milliseconds', inline=False)
    embed.add_field(name="Website the data is from:", value=" https://wiimmfi.de/stat?m=88", inline=False)
    embed.add_field(name="Want to report a bug, suggest a feature, or want to read/get the source code ?",
                    value="https://github.com/opale95/mkwiimmfi_status", inline=False)
    await ctx.send(embed=embed)


def get_player_count(sort=False):
    """Returns the table (DataFrame) of the number of players online from https://wiimmfi.de/stat?m=88, sorted alphabetically if asked so."""
    table = pd.read_html(io=STATUS_URL, match="Mario Kart Wii: Regions")[0]
    table.columns = ["Region & Mode", "N° of Players"]
    if sort:
        return table.sort_values(by="Region & Mode")
    return table


def get_regions_list():
    """"""
    regions = pd.read_html(io=REGIONS_URL, match="Name of region")[0]
    regions.drop(regions[regions[0] == "Region"].index, inplace=True)
    return regions[[0, 2]]


@client.command()
async def status(ctx):
    """Bot's main command that returns the number of players online, in each game region."""
    table = get_player_count(True)
    embed = discord.Embed(
        colour=discord.Colour.green())
    embed.set_author(name="Mario Kart Wii: Wiimmfi Online players")
    for row in table.itertuples():
        embed.add_field(name=row[1], value=row[2], inline=False)
    await ctx.send(embed=embed)


@client.command()
async def invite(ctx):
    """Command that returns an invite link."""
    await ctx.send(
        "I'd be glad to join your server ! Invite me by clicking on this link:\nhttps://discord.com/oauth2/authorize?client_id=" + CLIENT_ID + "&scope=bot&permissions=248897")

@client.command()
async def region(ctx, search):
    """Command to search regions ID's by name."""
    regions_list = get_regions_list()
    filtered_list = regions_list.loc[regions_list[2].str.contains(search, case=False)]
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name="Region ID search")
    for row in filtered_list.itertuples():
        embed.add_field(name=row[2], value=row[1])
    await ctx.send(embed=embed)


@client.command(name='subscribe', aliases=['sub'])
async def subscribe(ctx, *args):
    """"""
    text_channel = len(args) == 2 and args[0] == "channel"
    if text_channel:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            region_id = args[1]
            addressee = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can subscribe to be notified in Direct Message with the " + PREFIX + "sub REGION_ID command.")
            return
    elif len(args) == 1:
        region_id = args[0]
        addressee = "You"
    else:
        await ctx.send(
            "Error. Usage of sub command: " + PREFIX + "sub REGION_ID or " + PREFIX + "sub channel REGION_ID")
        return

    regions_list = get_regions_list()
    if regions_list[0].isin([region_id]).any():
        region_name = regions_list.loc[regions_list[0] == region_id][2].values[0]
        try:
            with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
                notification_subscribers_dict = json.load(notification_subscribers_json)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
                json.dump({}, new_file)
            notification_subscribers_dict = {}
        if text_channel:
            subscriber_id = str(ctx.channel.id)
        else:
            subscriber_id = str(ctx.author.id)

        if subscriber_id in notification_subscribers_dict:
            if region_id in notification_subscribers_dict[subscriber_id]:
                await ctx.send(
                    addressee + " already subscribed to be notified for the region " + region_id + " (" + region_name + ").")
                return
            else:
                notification_subscribers_dict[subscriber_id].append(region_id)
        else:
            notification_subscribers_dict[subscriber_id] = [region_id]

        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
            json.dump(notification_subscribers_dict, notification_subscribers_json)
        await ctx.send(
            addressee + " will now be notified when a player will join the first new room in region " + region_id + " (" + region_name + ") or when the last player in this region will left.")

    else:
        await ctx.send("The region ID " + str(
            region_id) + " does not exist. You can check the regions IDs there " + REGIONS_URL + ".")


@client.command(name='unsubscribe', aliases=['unsub'])
async def unsubscribe(ctx, *args):
    """"""
    text_channel = len(args) == 2 and args[0] == "channel"
    if text_channel:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            region_id = args[1]
            addressee = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can unsubscribe to be notified in Direct Message with the " + PREFIX + "unsub REGION_ID command.")
            return
    elif len(args) == 1:
        region_id = args[0]
        addressee = "You"
    else:
        await ctx.send(
            "Error. Usage of unsub command: " + PREFIX + "unsub REGION_ID or " + PREFIX + "sub channel REGION_ID")
        return

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    if text_channel:
        subscriber_id = str(ctx.channel.id)
    else:
        subscriber_id = str(ctx.author.id)

    if region_id == "all":
        if notification_subscribers_dict.pop(subscriber_id, None):
            await ctx.send(addressee + " will no longer receive any notification.")
        else:
            await ctx.send(addressee + " did not subscribe to any region notification.")
            return
    elif subscriber_id in notification_subscribers_dict:
        try:
            notification_subscribers_dict[subscriber_id].remove(region_id)
        except ValueError:
            await ctx.send(addressee + " did not subscribe to region " + region_id + " notifications.")
        else:
            regions_list = get_regions_list()
            region_name = regions_list.loc[regions_list[0] == region_id][2].values[0]
            if not notification_subscribers_dict[subscriber_id]:
                del notification_subscribers_dict[subscriber_id]
            await ctx.send(
                addressee + " will no longer be notified for region " + region_id + " (" + region_name + ").")
    else:
        await ctx.send(addressee + " did not subscribe to any region notification.")
        return

    with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
        json.dump(notification_subscribers_dict, notification_subscribers_json)


@client.command(name='subscriptions', aliases=['subs'])
async def subscriptions(ctx, *args):
    """"""
    text_channel = len(args) == 1 and args[0] == "channel"
    if text_channel:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            addressee = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can subscribe to be notified in Direct Message with the " + PREFIX + "sub REGION_ID command.")
            return
    elif len(args) == 0:
        addressee = "You"
    else:
        await ctx.send(
            "Error. Usage of subs command: " + PREFIX + "subs or " + PREFIX + "subs channel")
        return

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}
    if text_channel:
        subscriber_id = str(ctx.channel.id)
    else:
        subscriber_id = str(ctx.author.id)

    if subscriber_id in notification_subscribers_dict:
        regions_list = get_regions_list()
        embed = discord.Embed(colour=discord.Colour.green())
        embed.set_author(name=addressee + " subscribed to:")
        for region_id in notification_subscribers_dict[subscriber_id]:
            region_name = regions_list.loc[regions_list[0] == region_id][2].values[0]
            embed.add_field(name=region_id, value=region_name, inline=False)
        await ctx.send(embed=embed)

    else:
        await ctx.send(addressee + " didn't subscribe to any region notifications.")


async def bot_activity(table):
    """Updates the bot's activity with the total number of MKWii players online."""
    players_total = table.head(1).iat[0, 1]
    activity = discord.Activity(name='%d people playing Mario Kart Wii online.' % players_total,
                                type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)


async def notify(region_desc, message):
    """"""
    region = region_desc.partition("region ")[2].partition(" (")[0]
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    for addressee_id in notification_subscribers_dict:
        if region in notification_subscribers_dict[addressee_id]:
            if "start" in message:
                colour = discord.Colour.green()
            elif "waiting" in message:
                colour = discord.Colour.orange()
            else:
                colour = discord.Colour.red()
            embed = discord.Embed(colour=colour)
            embed.add_field(name=message + " ", value=region_desc.removeprefix("Players "))
            # await client.wait_until_ready()
            addressee = client.get_user(int(addressee_id))
            if addressee is None:
                addressee = client.get_channel(int(addressee_id))
            await addressee.send(embed=embed)


@tasks.loop(seconds=10)
async def check():
    """"""
    table = get_player_count()
    await bot_activity(table)

    global player_count_dict

    if len(player_count_dict) == 0:
        for row in table.itertuples():
            player_count_dict[row[1]] = row[2]

    else:
        new_dict = {}

        for row in table.itertuples():
            region_name = row[1]
            new_region_count = row[2]
            prev_region_count = player_count_dict.get(region_name)
            if prev_region_count:
                if prev_region_count == 1 and new_region_count > 1:
                    await notify(region_name, "A game with " + str(new_region_count) + " players is going to start")
                elif prev_region_count > 1 and new_region_count == 1:
                    await notify(region_name, "The game is over, but someone is waiting for a new game")
                del player_count_dict[region_name]
            else:
                if new_region_count == 1:
                    await notify(region_name, "Someone is waiting for a new game")
                else:
                    await notify(region_name, "A game with " + str(new_region_count) + " players is going to start")
            new_dict[region_name] = new_region_count
        for region_name in player_count_dict:
            await notify(region_name, "The game is over, there is nobody left to play")
        player_count_dict.clear()
        player_count_dict = new_dict


@client.event
async def on_ready():
    check.start()

@client.event
async def on_command_error(ctx, error):
    # emoji = '\N{EYES}'
    # await ctx.add_reaction(emoji)
    await ctx.send(f'Error. Try mkw:help ({error})')

client.run(TOKEN)
