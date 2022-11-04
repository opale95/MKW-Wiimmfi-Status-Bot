""" MKW Wiimmfi Status Bot
A Discord Bot (using the discord.py python library) that shows the current amount of people playing Mario Kart Wii
on the custom Wiimmfi servers.
Wiimmfi server website (from which the data is taken from): https://wiimmfi.de/stat?m=88
"""

import discord
from discord.ext import commands, tasks
import pandas as pd
import json
import time
import datetime
import requests

TOKEN = open("token.txt", "r").readline().removesuffix("\n")
CLIENT_ID = open("client_id.txt", "r").readline().removesuffix("\n")
PREFIX = "mkw:"

STATUS_URL = "https://wiimmfi.de/stat?m=80"
REGIONS_URL = "https://wiimmfi.de/reg-stat"
CUSTOM_REGIONS_URL = "https://wiimmfi.de/reg-list"
NOTIFICATION_SUBSCRIBERS_JSON = "notification_subscribers.json"

JSON_API_URL = "https://wiimmfi.de/stats/mkwx?m=json"
REGIONS_HTML = "regions.html"
CUSTOM_REGIONS_HTML = "custom_regions.html"

HIDDEN_REGIONS = {-9: "Private rooms",
                  99999: "World Wide (Battle)",
                  200027: "CTGP v1.03 (Count down)",
                  200028: "CTGP v1.03 (Count down)",
                  200033: "CTGP v1.03 (Count down)",
                  200040: "CTGP v1.03 (Count down)",
                  200046: "CTGP v1.03 (Count down)",
                  200047: "CTGP v1.03 (Count down)",
                  200052: "CTGP v1.03 (Count down)",
                  200059: "CTGP v1.03 (Count down)",
                  100501: "Bob-omb Blast Revolution",
                  100210: "Mario Kart Wii Deluxe v6.0 (Battle)",
                  200037: "CTGP v1.03 (Count down)"}

player_count_table = {}
regions_list = None
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
                    value="Search regions ID's by giving one or several words\nExample: mkw:region \"Mario Kart "
                          "Fusion\" or mkw:region fun", inline=False)
    embed.add_field(name='mkw:sub REGION_ID or mkw:sub channel REGION_ID',
                    value='Subscribe yourself to receive DM or the current channel (if you own the Manage Channels '
                          'rights) to be notified to regions events.\nExample: mkw:sub 870 or mkw:sub channel 870',
                    inline=False)
    embed.add_field(name='mkw:unsub REGION_ID|all or mkw:unsub REGION_ID|all',
                    value='Unsubcribe yourself or the current channel (if you own the Manage Channels rights) to '
                          'regions events notifications.\n '
                          'Example: mkw:unsub all or mkw:unsub 870 or mkw:unsub channel all or mkw:unsub channel 870',
                    inline=False)
    embed.add_field(name='mkw:subs or mkw:subs channel', value='Returns the region list for which you or the current '
                                                               'channel (if you own the Manage Channels rights) are '
                                                               'subscribed to.\n '
                                                               'Also shows after how many minutes "Someone joined a '
                                                               'room then left" messages are deleted."', inline=False)
    embed.add_field(name='mkw:clear or mkw:clear users or mkw:clear 1',
                    value='Removes all the bot messages in the channel or the users command requests (the bot needs '
                          'Manage Messages permissions to delete users requests) or messages about someone who joined '
                          'then left.', inline=False)
    embed.add_field(name='mkw:less or mkw:less MINUTES', value='Messages about someone who joined then left are '
                                                               'deleted after the number you put in place of MINUTES,'
                                                               ' or 15 minutes by default.', inline=False)
    embed.add_field(name='mkw:more', value='Messages about someone who joined then left are no longer automatically '
                                           'removed after some minutes.', inline=False)
    embed.add_field(name='mkw:invite', value='Returns a link to invite the bot in your server.', inline=False)
    embed.add_field(name='mkw:help', value='Returns this help list.', inline=False)
    embed.add_field(name='mkw:ping', value='Returns bot response time in milliseconds', inline=False)
    embed.add_field(name="Website the data is from:", value=" https://wiimmfi.de/stat?m=88", inline=False)
    embed.add_field(name="Want to report a bug, suggest a feature, or want to read/get the source code ?",
                    value="https://github.com/opale95/MKW-Wiimmfi-Status-Bot", inline=False)
    await ctx.send(embed=embed)


def get_player_count(sort=False):
    """Returns the table (DataFrame) of the number of players online from https://wiimmfi.de/stat?m=88,
    sorted alphabetically if asked so. """
    table = pd.read_html(io=STATUS_URL, match="Mario Kart Wii: Regions")[0]
    table.columns = ["Region & Mode", "N° of Players"]
    if sort:
        return table.sort_values(by="Region & Mode")
    return table


def get_player_count_json():
    response = requests.get(JSON_API_URL)

    try:
        mkwx_data = response.json()
    except json.decoder.JSONDecodeError as error:
        print("JSONDecodeError: ", error.msg)
        time.sleep(10)
        return get_player_count_json()
    else:
        table = {}
        for obj in mkwx_data:
            if obj["type"] == "room":
                if obj["region"] in table:
                    table[obj['region']] += obj['n_players']
                else:
                    table[obj['region']] = obj['n_players']

        return table


def get_regions_list():
    """"""
    # regions = pd.read_html(io=REGIONS_URL, match="Versus Race Regions of Mario Kart Wii")[0]
    regions = pd.read_html(io=REGIONS_HTML, match="Versus Race Regions of Mario Kart Wii")[0]
    regions = regions.iloc[:8, [0, 3]]
    regions.columns = ["ID", "Name"]
    regions = regions.astype(str)

    # custom = pd.read_html(io=CUSTOM_REGIONS_URL, match="Name of region")[0]
    custom = pd.read_html(io=CUSTOM_REGIONS_URL, match="Name of region")[0]
    custom.drop(custom[custom[0] == "Region"].index, inplace=True)
    custom = custom[[0, 2]]
    custom.columns = ["ID", "Name"]

    return pd.concat([regions, custom])
    # return regions.append(custom)


def get_region_name(region_id):
    name = HIDDEN_REGIONS.get(int(region_id))
    if name is not None:
        return name

    global regions_list
    match = regions_list.loc[regions_list["ID"].str.fullmatch(str(region_id))]
    if not match.empty:
        return match.values[0][1]
    return ""


@client.command()
async def status(ctx):
    """Bot's main command that returns the number of players online, in each game region."""
    global player_count_table
    # table = player_count_table.sort_values(by="Region & Mode")
    embed = discord.Embed(
        colour=discord.Colour.green(), title="Mario Kart Wii: Wiimmfi Online players",
        timestamp=datetime.datetime.utcnow())
    # for row in table.itertuples():
    total = 0
    for region_id in player_count_table:
        region_name = get_region_name(region_id)
        players_nb = player_count_table[region_id]
        total += players_nb
        # embed.add_field(name=row[1], value=row[2], inline=False)
        embed.add_field(name=region_name + " (region " + str(region_id) + ")",
                        value=str(players_nb) + " players", inline=False)
    embed.set_footer(text='---------------------------\n'+str(total)+' players on MKW')
    await ctx.send(embed=embed)


@client.command()
async def invite(ctx):
    """Command that returns an invitation link."""
    await ctx.send(
        "I'd be glad to join your server ! Invite me by clicking on this "
        "link:\nhttps://discord.com/oauth2/authorize?client_id=" + CLIENT_ID + "&scope=bot&permissions=257089")


@client.command()
async def region(ctx, search: str):
    """Command to search regions ID's by name."""
    global regions_list
    results = {}

    for region_id in HIDDEN_REGIONS:
        if search.casefold() in HIDDEN_REGIONS[region_id].casefold():
            results[region_id]=HIDDEN_REGIONS[region_id]

    filtered_list = regions_list.loc[regions_list["Name"].str.contains(search, case=False)]

    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name="Region ID search")

    if filtered_list.empty and not results:
        embed.colour = discord.Colour.red()
        embed.add_field(name="No result",
                        value="Regions list: https://wiimmfi.de/reg-stat or https://wiimmfi.de/reg-list")
    else:
        for region_id in results:
            embed.add_field(name=results[region_id], value=region_id)
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
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can subscribe to be notified in Direct Message "
                "with the " + PREFIX + "sub REGION_ID command.")
            return
    elif len(args) == 1:
        region_id = args[0]
        recipient = "You"
    else:
        await ctx.send(
            "Error. Usage of sub command: " + PREFIX + "sub REGION_ID or " + PREFIX + "sub channel REGION_ID")
        return

    global regions_list
    if int(region_id) in HIDDEN_REGIONS or regions_list["ID"].isin([region_id]).any():
        # region_name = regions_list.loc[regions_list["ID"] == region_id]["Name"].values[0]
        region_name = get_region_name(region_id)
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
            if region_id in notification_subscribers_dict[subscriber_id]["regions"]:
                await ctx.send(
                    recipient + " already subscribed to be notified for the region "
                    + region_id + " (" + region_name + ").")
                return
            else:
                notification_subscribers_dict[subscriber_id]["regions"].append(region_id)
        else:
            notification_subscribers_dict[subscriber_id] = {"regions": [region_id], "less": "0"}

        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
            json.dump(notification_subscribers_dict, notification_subscribers_json)
        await ctx.send(
            recipient + " will now be notified when players will connect to region "
            + region_id + " (" + region_name + ").")

    else:
        await ctx.send("The region ID " + str(
            region_id) + " does not exist. You can search regions IDs with ```mkw:region \"words to search\"``` or "
                         "```mkw:region word_to_search```")


@client.command(name='unsubscribe', aliases=['unsub'])
async def unsubscribe(ctx, *args):
    """"""
    text_channel = len(args) == 2 and args[0] == "channel"
    if text_channel:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            region_id = args[1]
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can unsubscribe to be notified in Direct Message "
                "with the " + PREFIX + "unsub REGION_ID command.")
            return
    elif len(args) == 1:
        region_id = args[0]
        recipient = "You"
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
            await ctx.send(recipient + " will no longer receive any notification.")
        else:
            await ctx.send(recipient + " did not subscribe to any region notification.")
            return
    elif subscriber_id in notification_subscribers_dict:
        try:
            notification_subscribers_dict[subscriber_id]["regions"].remove(region_id)
        except ValueError:
            await ctx.send(recipient + " did not subscribe to region " + region_id + " notifications.")
        else:
            global regions_list
            # region_name = regions_list.loc[regions_list["ID"] == region_id]["Name"].values[0]
            region_name = get_region_name(region_id)
            if not notification_subscribers_dict[subscriber_id]["regions"]:
                del notification_subscribers_dict[subscriber_id]
            await ctx.send(
                recipient + " will no longer be notified for region " + region_id + " (" + region_name + ").")
    else:
        await ctx.send(recipient + " did not subscribe to any region notification.")
        return

    with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
        json.dump(notification_subscribers_dict, notification_subscribers_json)


@client.command(name='subscriptions', aliases=['subs'])
async def subscriptions(ctx, *args):
    """"""
    text_channel = len(args) == 1 and args[0] == "channel"
    if text_channel:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel.")
            return
    elif len(args) == 0:
        recipient = "You"
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
        global regions_list
        embed = discord.Embed(colour=discord.Colour.green())
        embed.set_author(name=recipient + " subscribed to:")
        delay = notification_subscribers_dict[subscriber_id]["less"]
        if delay != "0":
            embed.set_footer(text="\"Someone joined a room then left\" notifications are deleted after " +
                                  notification_subscribers_dict[subscriber_id]["less"] + " minutes.")
        else:
            embed.set_footer(text="\"Someone joined a room then left\" notifications won't be automatically deleted.")
        for region_id in notification_subscribers_dict[subscriber_id]["regions"]:
            # region_name = regions_list.loc[regions_list["ID"] == region_id]["Name"].values[0]
            region_name = get_region_name(region_id)
            embed.add_field(name=region_id, value=region_name, inline=False)
        await ctx.send(embed=embed)

    else:
        await ctx.send(recipient + " didn't subscribe to any region notifications.")


async def bot_activity(table):
    """Updates the bot's activity with the total number of MKWii players online."""
    # players_total = table.head(1).iat[0, 1]
    players_total = 0
    for region_id in table:
        players_total += table[region_id]
    activity = discord.Activity(name='%d people playing Mario Kart Wii online.' % players_total,
                                type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)


# async def notify(region_desc, message_content, messages):
async def notify(region_id, notification_content, messages):
    """"""
    # region_id = region_desc.partition("region ")[2].partition(" (")[0]
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    if "waiting" in notification_content:
        colour = discord.Colour.orange()
    elif "left" in notification_content:
        colour = discord.Colour.red()
    else:
        colour = discord.Colour.green()
    embed = discord.Embed(colour=colour, timestamp=datetime.datetime.utcnow())
    # embed.add_field(name=message_content + " ", value=region_desc.removeprefix("Players "))
    region_name = get_region_name(region_id)
    embed.add_field(name=notification_content + " ", value="in  " + region_name + " (region " + str(region_id) + ")")

    messages_channel_id = []
    if len(messages) != 0:
        for message in messages:
            if "then left" in notification_content:
                if message.channel.type == discord.ChannelType.private:
                    recipient_id = str(message.channel.recipient.id)
                else:
                    recipient_id = str(message.channel.id)
                if recipient_id in notification_subscribers_dict:
                    delay = notification_subscribers_dict[recipient_id]["less"]
                else:
                    delay = "0"
                    print("RECIPIENT " + recipient_id + " no longer subscribed.")
            else:
                delay = "0"
            try:
                if delay == "0":
                    await message.edit(embed=embed)
                else:
                    await message.edit(embed=embed, delete_after=float(delay) * 60)
            except (discord.NotFound, discord.Forbidden) as error:
                print("ERROR: ", error.text, "\nMESSAGE.CHANNEL.ID: ", message.channel.id)
                messages.remove(message)
            except (discord.DiscordServerError, discord.HTTPException) as error:
                print("ERROR: ", error.text, "\nMESSAGE.CHANNEL.ID: ", message.channel.id)
            except Exception as error:
                print("ERROR: ", error)
            else:
                messages_channel_id.append(message.channel.id)

    to_delete = []
    for recipient_id in notification_subscribers_dict:
        if str(region_id) in notification_subscribers_dict[recipient_id]["regions"]:
            recipient = client.get_user(int(recipient_id))
            if recipient is None:
                recipient = client.get_channel(int(recipient_id))
                if recipient:
                    channel_id = recipient.id
                else:
                    channel_id = None
            else:
                dm_channel = recipient.dm_channel
                if dm_channel:
                    channel_id = recipient.dm_channel.id
                else:
                    channel_id = None
            if recipient and channel_id not in messages_channel_id:
                delay = notification_subscribers_dict[recipient_id]["less"]
                try:
                    if "then left" in notification_content and delay != "0":
                        message_object = await recipient.send(embed=embed, delete_after=float(delay) * 60)
                    else:
                        message_object = await recipient.send(embed=embed)
                except discord.Forbidden as error:
                    print("Forbidden: ", error.text, "\nRECIPIENT: ", recipient_id)
                    to_delete.append(recipient_id)
                except (discord.DiscordServerError, discord.Forbidden, discord.NotFound, discord.HTTPException)\
                        as error:
                    print("ERROR: ", error.text, "\nRECIPIENT: ", recipient_id)
                else:
                    messages.append(message_object)
    for recipient_id in to_delete:
        del notification_subscribers_dict[recipient_id]
    if to_delete:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
            json.dump(notification_subscribers_dict, notification_subscribers_json)


@tasks.loop(seconds=10)
async def check():
    """"""
    global player_count_table, regions_list, player_count_dict

    # player_count_table = get_player_count()
    player_count_table = get_player_count_json()
    regions_list = get_regions_list()
    await bot_activity(player_count_table)

    new_dict = {}

    # for row in player_count_table.itertuples():
    for region_id in player_count_table:
        # region_desc = row[1]
        # new_region_count = row[2]
        new_region_count = player_count_table[region_id]
        # data = player_count_dict.get(region_desc)
        data = player_count_dict.get(region_id)

        if data:
            prev_region_count = data["count"]
            messages = data["messages"]
            max_region_count = data["max"]
            start = data["start"]
            if prev_region_count != new_region_count:
                if new_region_count > max_region_count:
                    max_region_count = new_region_count
                if new_region_count == 1:
                    # await notify(region_desc, "The game is over, but someone is waiting for a new game", messages)
                    await notify(region_id, "The game is over, but someone is waiting for a new game", messages)
                else:
                    # await notify(region_desc, str(new_region_count) + " players", messages)
                    await notify(region_id, str(new_region_count) + " players", messages)
            # del player_count_dict[region_desc]
            del player_count_dict[region_id]
        else:
            max_region_count = new_region_count
            messages = []
            start = time.time()
            if new_region_count == 1:
                # await notify(region_desc, "Someone is waiting for a new game", messages)
                await notify(region_id, "Someone is waiting for a new game", messages)
            else:
                # await notify(region_desc, str(new_region_count) + " players", messages)
                await notify(region_id, str(new_region_count) + " players", messages)
        # new_dict[region_desc] = {"count": new_region_count, "messages": messages, "max": max_region_count,
        # "start": start}
        new_dict[region_id] = {"count": new_region_count, "messages": messages, "max": max_region_count, "start": start}
    for region_desc in player_count_dict:
        max_region_count = player_count_dict[region_desc]["max"]
        if max_region_count > 1:
            await notify(region_desc,
                         "The game is over, there is nobody left to play.\nDuration: "
                         + str(datetime.timedelta(
                             seconds=time.time() - player_count_dict[region_desc]["start"])).partition(
                             '.')[0]
                         + "\nMaximum simultaneous players: " + str(player_count_dict[region_desc]["max"]),
                         player_count_dict[region_desc]["messages"])
        else:
            await notify(region_desc,
                         "Someone joined a room then left.\nDuration: "
                         + str(datetime.timedelta(
                             seconds=time.time() - player_count_dict[region_desc]["start"])).partition('.')[0],
                         player_count_dict[region_desc]["messages"])
    player_count_dict.clear()
    player_count_dict = new_dict


@client.command()
async def clear(ctx, *args):
    """"""
    if ctx.channel.type != discord.ChannelType.private and not ctx.author.permissions_in(ctx.channel).manage_channels:
        await ctx.send(
            "You have not the right to manage this channel.")
        return
    if len(args) > 1 or (len(args) == 1 and args[0] not in ("users", "1")):
        await ctx.send("clear command usage: ```mkw:clear``` or ```mkw:clear users``` or ```mkw:clear 1```")
        return
    users = args and args[0] == "users"
    _1p = args and args[0] == "1"
    if users:
        if ctx.channel.type == discord.ChannelType.private:
            await ctx.send("I can't remove other messages than mine in a Private Message channel.")
            return
        clean_message = await ctx.send(
            "I will remove all previous command requests users sent in this channel, it will take some time !")
    elif _1p:
        clean_message = await ctx.send(
            "All previous messages about one player joining then leaving a region will be removed, it will take some "
            "time !")
    else:
        clean_message = await ctx.send(
            "I will remove all previous messages i sent in this channel, it will take some time !")
    read = 0
    found = 0
    messages = await ctx.history(before=clean_message).flatten()
    while len(messages) > 0:
        for message in messages:
            read = read + 1
            if (users and message.author != client.user and PREFIX in message.content) \
                    or (_1p and message.author == client.user
                        and any(match in (message.embeds[0].fields[0].name if message.embeds else []) for match in
                                ["Someone", "players: 1"])) \
                    or (not (users or _1p) and message.author == client.user):
                found = found + 1
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound) as error:
                    print("ERROR: ", error.text, "\nCHANNEL_ID: ", message.channel.id)
        messages = await ctx.history(before=messages[len(messages) - 1]).flatten()
    await clean_message.edit(
        content="Cleaning done ! I have read " + str(read) + " messages and deleted " + str(found)
                + ".\nThis message will be removed in 5 minutes.", delete_after=300.0)
    await ctx.message.delete(delay=300.0)


def v2_to_v3_json_conv():
    """"""
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No JSON to convert.")
    else:
        try:
            item = notification_subscribers_dict.popitem()
        except KeyError:
            print("JSON is empty. Nothing to convert.")
        else:
            if type(item[1]) == list:
                for recipient in notification_subscribers_dict:
                    notification_subscribers_dict[recipient] = {"regions": notification_subscribers_dict[recipient],
                                                                "less": "0"}
                with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
                    json.dump(notification_subscribers_dict, notification_subscribers_json)
            else:
                print("JSON is already OK")


@client.command()
async def less(ctx, delay="15"):
    """"""
    private = ctx.channel.type == discord.ChannelType.private
    if not private and not ctx.author.permissions_in(ctx.channel).manage_channels:
        await ctx.send(
            "You have not the right to manage this channel.")
        return
    if not delay.isdigit():
        await ctx.send(
            "less command usage: ```mkw:less``` or ```mkw:less DELAY``` (replace DELAY by the number of minutes you "
            "want the messages to be deleted after.")
        return
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    if private:
        subscriber_id = str(ctx.author.id)
        recipient = "You"
    else:
        subscriber_id = str(ctx.channel.id)
        recipient = "This channel"

    if subscriber_id in notification_subscribers_dict:
        notification_subscribers_dict[subscriber_id]["less"] = delay
    else:
        await ctx.send(recipient + " didn't subscribe to any region notifications.")
        return

    with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
        json.dump(notification_subscribers_dict, notification_subscribers_json)
    await ctx.send(
        "Messages i will send about a player joining then leaving a region will now be deleted after " + delay +
        " minutes.")


@client.command()
async def more(ctx):
    """"""
    private = ctx.channel.type == discord.ChannelType.private
    if not private and not ctx.author.permissions_in(ctx.channel).manage_channels:
        await ctx.send(
            "You have not the right to manage this channel.")
        return
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    if private:
        subscriber_id = str(ctx.author.id)
        recipient = "You"
    else:
        subscriber_id = str(ctx.channel.id)
        recipient = "This channel"

    if subscriber_id in notification_subscribers_dict:
        notification_subscribers_dict[subscriber_id]["less"] = "0"
    else:
        await ctx.send(recipient + " didn't subscribe to any region notifications.")
        return

    with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
        json.dump(notification_subscribers_dict, notification_subscribers_json)
    await ctx.send("From now on, notifications about a player joining then leaving a region won't be deleted.")


@client.event
async def on_ready():
    # v2_to_v3_json_conv()

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)

    print("on_ready() as been used, must be a reconnection to Discord, or maybe you rebooted/restarted the bot ?")
    #     notification_subscribers_dict = {}
    #
    # for recipient_id in notification_subscribers_dict:
    #     recipient = client.get_user(int(recipient_id))
    #     if recipient is None:
    #         recipient = client.get_channel(int(recipient_id))
    #     try:
    #         # await recipient.send("I just rebooted ! I should be working fine from now on.")
    #         print(
    #             "on_ready() as been used, must be a reconnection to Discord, or maybe you rebooted/restarted the bot ?")
    #     except (discord.Forbidden, discord.NotFound) as error:
    #         print("ERROR: ", error.text, "\nRECIPIENT: ", recipient_id)
    #     except AttributeError as error:
    #         print("client.get_channel() and client.get_user() both returned None. RECIPIENT_ID: " + recipient_id)

    if not check.is_running():
        check.start()


@client.event
async def on_command_error(ctx, error):
    try:
        await ctx.send(f'Error. Try mkw:help ({error})')
    except discord.Forbidden as error:
        print("Forbidden: ", error.text, "\nCHANNEL_ID: ", ctx.channel.id)


client.run(TOKEN)
