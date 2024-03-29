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

HIDDEN_REGIONS = {-9: "Private rooms"}

BATTLE_ID_BASE = 100000
COUNTDOWN_ID_BASE = 200000

player_count_table = {}
regions_list = None
player_count_dict = {}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

guilds_count = 0


@bot.hybrid_command()
async def ping(ctx):
    """Returns the bot's latency in milliseconds."""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms ')


@bot.hybrid_command()
@commands.is_owner()
async def bot_message(ctx,  message):
    """Command that let the bot owner send info to subscribers."""
    # print(str(ctx.author.id) + " | " + str(bot.owner_id))
    # if ctx.author.id == bot.owner_id:
    # if token == TOKEN:
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
    else:
        sent_count = 0
        error_count = 0
        for recipient_id in notification_subscribers_dict:
            recipient = bot.get_user(int(recipient_id))
            if recipient is None:
                recipient = bot.get_channel(int(recipient_id))
            if recipient:
                sent_count += 1
                await recipient.send(message)
            else:
                error_count += 1
        await ctx.send("Sent " + str(sent_count) + " " + str(error_count) + " recipients unreachable from their ID.")
    # else:
        # await ctx.send("Wrong token.")


bot.remove_command('help')


@bot.hybrid_command(pass_context=True)
async def help(ctx):
    """Returns an embedded list and details of commands, and some additional information."""
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='/status', value='Shows how many players are online, and in which game regions.',
                    inline=False)
    embed.add_field(name='/region "MANY WORDS" or /region WORD',
                    value="Search regions ID's by giving one or several words\nExample: /region \"Mario Kart "
                          "Fusion\" or /region fun", inline=False)
    embed.add_field(name='/subscribe dm REGION_ID or /subscribe channel REGION_ID',
                    value='Subscribe yourself to receive DM or the current channel (if you own the Manage Channels '
                          'rights) to be notified to regions events.\nExample: /subscribe dm 870 or /subscribe channel 870',
                    inline=False)
    embed.add_field(name='/unsubscribe dm REGION_ID|all or /unsubscribe channel REGION_ID|all',
                    value='Unsubcribe yourself or the current channel (if you own the Manage Channels rights) to '
                          'regions events notifications.\n '
                          'Example: /unsubscribe dm all or /unsubscribe dm 870 or /unsubscribe channel all or /unsubscribe channel 870',
                    inline=False)
    embed.add_field(name='/subscriptions dm or /subscriptions channel', value='Returns the region list for which you or the current '
                                                               'channel (if you own the Manage Channels rights) are '
                                                               'subscribed to.\n '
                                                               'Also shows after how many minutes "Someone joined a '
                                                               'room then left" messages are deleted."', inline=False)
    embed.add_field(name='/clear bot or /clear users or /clear 1',
                    value='Removes all the bot messages in the channel or the users command requests (the bot needs '
                          'Manage Messages permissions to delete users requests) or messages about someone who joined '
                          'then left.', inline=False)
    embed.add_field(name='/less or /less MINUTES', value='Messages about someone who joined then left are '
                                                               'deleted after the number you put in place of MINUTES,'
                                                               ' or 15 minutes by default.', inline=False)
    embed.add_field(name='/more', value='Messages about someone who joined then left are no longer automatically '
                                           'removed after some minutes.', inline=False)
    embed.add_field(name='/invite', value='Returns a link to invite the bot in your server.', inline=False)
    embed.add_field(name='/help', value='Returns this help list.', inline=False)
    embed.add_field(name='/ping', value='Returns bot response time in milliseconds', inline=False)
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
    new_columns = ["ID", "Name"]
    # regions = pd.read_html(io=REGIONS_URL, match="Versus Race Regions of Mario Kart Wii")[0]
    regions = pd.read_html(io=REGIONS_HTML, match="Versus Race Regions of Mario Kart Wii")[0]
    regions = regions.iloc[:6, [0, 3]]
    regions.columns = new_columns
    regions = regions.astype(str)

    # custom = pd.read_html(io=CUSTOM_REGIONS_URL, match="Name of region")[0]
    custom = pd.read_html(io=CUSTOM_REGIONS_HTML, match="Name of region", encoding='utf8')[0]
    custom.drop(custom[custom[0] == "Region"].index, inplace=True)
    #custom = custom[[0, 2]]
    custom = custom.iloc[0:,[0,2,3,4,5]]
    custom.columns = ["ID", "Name", "vs", "bt", "cd"]
    custom = custom.astype(str)

    updated_list = []
    rows = regions.itertuples()
    for row in rows:
        updated_list.append([row.ID, row.Name])
        updated_list.append([str(int(row.ID)+BATTLE_ID_BASE), row.Name+' (Battle)'])

    rows = custom.itertuples()
    for row in rows:
        if row.bt == '✓':
            updated_list.append([str(int(row.ID)+BATTLE_ID_BASE), row.Name+' (Battle)'])
        if row.cd == '✓':
            updated_list.append([str(int(row.ID)+COUNTDOWN_ID_BASE), row.Name+' (Countdown)'])

    custom.drop(columns=["vs", "bt", "cd"])

    return pd.concat([custom, pd.DataFrame(updated_list, columns=new_columns)])
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


@bot.hybrid_command()
async def status(ctx):
    """Bot's main command that returns the number of players online, in each game region."""
    global player_count_table
    # table = player_count_table.sort_values(by="Region & Mode")
    embed = discord.Embed(
        colour=discord.Colour.green(), title="Mario Kart Wii: Wiimmfi Online players",
        timestamp=datetime.datetime.now())
    # for row in table.itertuples():
    total = 0
    for region_id in player_count_table:
        region_name = get_region_name(region_id)
        players_nb = player_count_table[region_id]
        total += players_nb
        # embed.add_field(name=row[1], value=row[2], inline=False)
        embed.add_field(name=region_name + " (region " + str(region_id) + ")",
                        value=str(players_nb) + " players", inline=False)
    embed.set_footer(text='------------------------------------------------------\n'
        + str(total)+' players on MKW.\nBot used by ' + str(guilds_count) + " servers.")
    await ctx.send(embed=embed)


@bot.hybrid_command()
async def invite(ctx):
    """Returns an invitation link."""
    await ctx.send(
        "I'd be glad to join your server ! Invite me by clicking on this "
        "link:\nhttps://discord.com/oauth2/authorize?client_id=" + CLIENT_ID + "&scope=bot&permissions=2147707905")


@bot.hybrid_command()
async def region(ctx, search: str):
    """Search regions ID's by name."""
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


@bot.hybrid_command(name='subscribe', aliases=['sub'])
async def subscribe(ctx, channel_type, region_id):
    """Request to be notified by the bot when players are online in a specific region."""
    if channel_type == "channel":
        if ctx.channel.permissions_for(ctx.author).manage_channels:
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can subscribe to be notified in Direct Message "
                "with the " + PREFIX + "sub dm REGION_ID command.")
            return
    elif channel_type == "dm":
        recipient = "You"
    else:
        await ctx.send(
            "Error. Usage of sub command: " + PREFIX + "sub dm REGION_ID or " + PREFIX + "sub channel REGION_ID")
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
        if channel_type == "channel":
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
            notification_subscribers_dict[subscriber_id] = {"regions": [region_id], "less": "0", "type": channel_type}

        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
            json.dump(notification_subscribers_dict, notification_subscribers_json)
        await ctx.send(
            recipient + " will now be notified when players will connect to region "
            + region_id + " (" + region_name + ").")

    else:
        await ctx.send("The region ID " + str(
            region_id) + " does not exist. You can search regions IDs with ```/region \"words to search\"``` or "
                         "```/region word_to_search```")


@bot.hybrid_command(name='unsubscribe', aliases=['unsub'])
async def unsubscribe(ctx, channel_type, region_id):
    """Request to not be notified anymore by the bot."""
    if channel_type == "channel":
        if ctx.channel.permissions_for(ctx.author).manage_channels:
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel. You can unsubscribe to be notified in Direct Message "
                "with the " + PREFIX + "unsub dm REGION_ID command.")
            return
    elif channel_type == "dm":
        recipient = "You"
    else:
        await ctx.send(
            "Error. Usage of unsub command: " + PREFIX + "unsub dm REGION_ID or " + PREFIX + "unsub channel REGION_ID")
        return

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}

    if channel_type == "channel":
        subscriber_id = str(ctx.channel.id)
    else:
        subscriber_id = str(ctx.author.id)

    if subscriber_id in notification_subscribers_dict and notification_subscribers_dict[subscriber_id]["type"] == channel_type:
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


@bot.hybrid_command(name='subscriptions', aliases=['subs'])
async def subscriptions(ctx, channel_type):
    """List the regions a user/channel has requested to be notified about."""
    if channel_type == "channel":
        if ctx.channel.permissions_for(ctx.author).manage_channels:
            recipient = "This channel"
        else:
            await ctx.send(
                "You have not the right to manage this channel.")
            return
    elif channel_type == "dm":
        recipient = "You"
    else:
        await ctx.send(
            "Error. Usage of subs command: " + PREFIX + "subs dm or " + PREFIX + "subs channel")
        return

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)
        notification_subscribers_dict = {}
    if channel_type == "channel":
        subscriber_id = str(ctx.channel.id)
    else:
        subscriber_id = str(ctx.author.id)

    if subscriber_id in notification_subscribers_dict and notification_subscribers_dict[subscriber_id]["type"] == channel_type:
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
    await bot.change_presence(activity=activity)


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
    embed = discord.Embed(colour=colour, timestamp=datetime.datetime.now())
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
            recipient_type = notification_subscribers_dict[recipient_id]["type"]
            recipient = None
            channel_id = None
            if recipient_type == "channel":
                recipient = bot.get_channel(int(recipient_id))
                if recipient:
                    channel_id = recipient.id
                else:
                    channel_id = None
            elif recipient_type == "dm":
                coro = bot.fetch_user(int(recipient_id))
                try:
                    recipient = await coro
                except discord.DiscordException as error:
                    print("ERROR: ", error.text, "\nRECIPIENT: ", recipient_id)
                if recipient:
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
                except discord.DiscordException as error:
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


def is_request(message):
    """"""
    return message.author != bot.user and PREFIX in message.content


def is_1p(message):
    """"""
    return message.author == bot.user \
        and any(match in (message.embeds[0].fields[0].name if message.embeds else []) for match in ["Someone", "players: 1"])


def is_bot(message):
    """"""
    return message.author == bot.user


@bot.hybrid_command()
async def clear(ctx, message_type):
    """Removes the 25 last bot/user request messages."""
    limit = 25
    if ctx.channel.type == discord.ChannelType.private:
        await ctx.send("You can't use this command in private channels.")
        return
    elif not ctx.channel.permissions_for(ctx.author).manage_channels:
        await ctx.send("You have not the right to manage this channel.")
        return
    if message_type not in ("bot", "users", "1"):
        await ctx.send("clear command usage: ```/clear bot``` or ```/clear users``` or ```/clear 1```")
        return
    if message_type == "users":
        if ctx.channel.type == discord.ChannelType.private:
            await ctx.send("I can't remove other messages than mine in a Private Message channel.")
            return
        clean_message = await ctx.send(
            "I will remove the " + str(limit) + " previous command requests users sent in this channel, it will take some time !")
    elif message_type == "1":
        clean_message = await ctx.send(
            "The " + str(limit) + " previous messages about one player joining then leaving a region will be removed, it will take some "
            "time !")
    else:
        clean_message = await ctx.send(
            "I will remove the " + str(limit) + " previous messages i sent in this channel, it will take some time !")

    # read = 0
    # found = 0
    # messages = await ctx.history(before=clean_message).flatten()
    # while len(messages) > 0:
    #     for message in messages:
    #         read = read + 1
    #         if (users and message.author != client.user and PREFIX in message.content) \
    #                 or (_1p and message.author == client.user
    #                     and any(match in (message.embeds[0].fields[0].name if message.embeds else []) for match in
    #                             ["Someone", "players: 1"])) \
    #                 or (not (users or _1p) and message.author == client.user):
    #             found = found + 1
    #             try:
    #                 await message.delete()
    #             except (discord.Forbidden, discord.NotFound) as error:
    #                 print("ERROR: ", error.text, "\nCHANNEL_ID: ", message.channel.id)
    #     messages = await ctx.history(before=messages[len(messages) - 1]).flatten()
    # await clean_message.edit(
    #     content="Cleaning done ! I have read " + str(read) + " messages and deleted " + str(found)
    #             + ".\nThis message will be removed in 5 minutes.", delete_after=300.0)
    try:
        if message_type == "users":
            deleted = await ctx.channel.purge(check=is_request, limit=limit, before=clean_message)
        elif message_type == "1":
            deleted = await ctx.channel.purge(check=is_1p, limit=limit, before=clean_message)
        else:
            deleted = await ctx.channel.purge(check=is_bot, limit=limit, before=clean_message)

        await clean_message.edit(
            content="Cleaning done ! I deleted " + str(len(deleted))
                    + ".\nThis message will be removed in 5 minutes.", delete_after=300.0)

        await ctx.message.delete(delay=300.0)

    except (discord.Forbidden, discord.NotFound) as error:
        print("ERROR: ", error.text, "\nCHANNEL_ID: ", ctx.channel.id)


@bot.hybrid_command()
async def less(ctx, delay="15"):
    """Pick a time in minutes after which notifications about a single player are deleted."""
    private = ctx.channel.type == discord.ChannelType.private
    if not private and not ctx.channel.permissions_for(ctx.author).manage_channels:
        await ctx.send(
            "You have not the right to manage this channel.")
        return
    if not delay.isdigit():
        await ctx.send(
            "less command usage: ```/less``` or ```/less DELAY``` (replace DELAY by the number of minutes you "
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


@bot.hybrid_command()
async def more(ctx):
    """Message about a single player waiting for a game won't be deleted anymore."""
    private = ctx.channel.type == discord.ChannelType.private
    if not private and not ctx.channel.permissions_for(ctx.author).manage_channels:
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


@bot.event
async def on_ready():
    global guilds_count
    guilds_count = len(bot.guilds)

    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            notification_subscribers_dict = json.load(notification_subscribers_json)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
            json.dump({}, new_file)

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
        await bot.tree.sync()
        check.start()


@bot.event
async def on_command_error(ctx, error):
    try:
        await ctx.send(f'Error. Try /help ({error})')
    except discord.Forbidden as error:
        print("Forbidden: ", error.text, "\nCHANNEL_ID: ", ctx.channel.id)


bot.run(TOKEN)
