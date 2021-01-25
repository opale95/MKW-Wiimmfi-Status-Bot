""" mkwiimmfi_status v1.0.1
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

client = commands.Bot(command_prefix=PREFIX)


@client.command()
async def ping(ctx):
    """Returns the bot's latency in milliseconds."""
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms ')


client.remove_command('help')


@client.command(pass_context=True)
async def help(ctx):
    """Help command that returns an embedded list and details of commands, and some additional information."""
    embed = discord.Embed(
        colour=discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='mkw:status', value='Shows how many players are online, and in which game regions', inline=False)
    embed.add_field(name='mkw:help', value='Returns this help list', inline=False)
    embed.add_field(name='mkw:ping', value='Returns bot response time in milliseconds', inline=False)
    embed.add_field(name='mkw:invite', value='Returns a link to invite the bot in your server', inline=False)
    embed.add_field(name="Website the data is from:", value=" https://wiimmfi.de/stat?m=88", inline=False)
    embed.add_field(name="Want to report a bug, suggest a feature, or want to read/get the source code ?", value="https://github.com/opale95/mkwiimmfi_status", inline=False)
    await ctx.send(embed=embed)


def get_regions_players_nb(sort=True):
    """Returns the table (DataFrame) of the number of players online from https://wiimmfi.de/stat?m=88, sorted alphabetically if asked so."""
    table = pd.read_html(io=STATUS_URL, match="Mario Kart Wii: Regions")[0]
    if sort:
        return table.sort_values(by=('Mario Kart Wii: Regions', 'Description'))
    return table


def get_regions_list():
    """"""
    regions = pd.read_html(io=REGIONS_URL, match="Name of region")[0]
    regions.drop(regions[regions[0] == "Region"].index, inplace=True)
    return regions[0]


@client.command()
async def status(ctx):
    """Bot's main command that returns the number of players online, in each game region."""
    table = get_regions_players_nb(True)
    embed = discord.Embed(
        colour=discord.Colour.green())
    embed.set_author(name="Mario Kart Wii: Wiimmfi Online players")
    for index, row in table.iterrows():
        embed.add_field(name=row[0], value=row[1], inline=False)
    await ctx.send(embed=embed)


@client.command()
async def invite(ctx):
    """Command that returns an invite link."""
    await ctx.send("I'd be glad to join your server ! Invite me by clicking on this link:\nhttps://discord.com/oauth2/authorize?client_id="+CLIENT_ID+"&scope=bot&permissions=248897")


@tasks.loop(minutes=1)
async def bot_activity():
    """Task updating the bot's activity with the total number of MKWii players online."""
    table = get_regions_players_nb()
    players_count = table.tail(1).iat[0, 1]
    activity = discord.Activity(name='%d people playing Mario Kart Wii online.' % players_count,
                                type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)


@client.command(name='subscribe', aliases=['sub'])
async def subscribe(ctx, *args):
    """"""
    channel_mode = len(args) == 2 and args[0] == "channel"
    if channel_mode:
        if ctx.author.permissions_in(ctx.channel).manage_channels:
            region = args[1]
            addressee = "This channel"
        else:
            await ctx.send("You have not the right to manage this channel.")
            return
    elif len(args) == 1:
        region = args[0]
        addressee = "You"
    else:
        await ctx.send("Error. Usage of sub command: " + PREFIX + "sub REGION_ID or " + PREFIX + "sub channel REGION_ID")
        return

    if get_regions_list().isin([region]).any():
        try:
            with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
                try:
                    notification_subscribers_dict = json.load(notification_subscribers_json)
                    print("Dictionnaire lu depuis le JSON: ", notification_subscribers_dict)
                except json.JSONDecodeError:
                    # await ctx.send("I have problems using my database, please try again and if the error persists, contact the moderator or developer.")
                    with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
                        json.dump({}, new_file)
        except FileNotFoundError:
            await ctx.send("Oops, i had to create my database, please try the command again.")
            with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as new_file:
                json.dump({}, new_file)

        else:
            if channel_mode:
                channel_id = str(ctx.channel.id)
            else:
                await ctx.message.author.send("Hello! You requested to be notified for the region " + region + ".")
                channel_id = str(ctx.author.dm_channel.id)

            if channel_id in notification_subscribers_dict:
                if region in notification_subscribers_dict[channel_id]:
                    await ctx.send(addressee + " already subscribed to be notified for this region.")
                    return
                else:
                    notification_subscribers_dict[channel_id].append(region)
                print("Le salon est dans le dico !")
            else:
                notification_subscribers_dict[channel_id] = [region]

            with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
                json.dump(notification_subscribers_dict, notification_subscribers_json)
            await ctx.send(addressee + " will now be notified when a player will join the first new room in this region or when the last player in this region will left.")
            print("Dictionnaire après modif. écrit dans le JSON: ", notification_subscribers_dict)

    else:
        await ctx.send("The region ID " + str(region) + " does not exist. You can check the regions IDs there " + REGIONS_URL + ".")


@client.command(name='unsubscribe', aliases=['unsub'])
@commands.has_permissions(manage_channels=True)
async def unsubscribe(ctx, region):
    """"""
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            try:
                notification_subscribers_dict = json.load(notification_subscribers_json)
                print("Dictionnaire lu depuis le JSON: ", notification_subscribers_dict)
            except json.JSONDecodeError:
                await ctx.send("I have problems using my database, please try again and if the error persists, contact the moderator or developer.")
                print("Problème de lecture du JSON, le fichier est inexistant ou vide ?")
    except FileNotFoundError:
        await ctx.send("I have problems using my database, please try again and if the error persists, contact the moderator or developer.")

    else:
        channel_id = str(ctx.message.channel.id)
        if channel_id in notification_subscribers_dict:
            try:
                notification_subscribers_dict[channel_id].remove(region)
            except ValueError:
                await ctx.send("You were not subscribed to this region notifications")
            else:
                if not notification_subscribers_dict[channel_id]:
                    del notification_subscribers_dict[channel_id]
                with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
                    json.dump(notification_subscribers_dict, notification_subscribers_json)
                await ctx.send("Region " + region + " removed from your subscriptions.")
        else:
            await ctx.send("You will no longer receive notifications from region " + region + ".")

        print("Dictionnaire après modif. écrit dans le JSON: ", notification_subscribers_dict)


@client.command()
async def unsubscribe_dm(ctx, region):
    """"""
    try:
        with open(NOTIFICATION_SUBSCRIBERS_JSON, "r") as notification_subscribers_json:
            try:
                notification_subscribers_dict = json.load(notification_subscribers_json)
                print("Dictionnaire lu depuis le JSON: ", notification_subscribers_dict)
            except json.JSONDecodeError:
                await ctx.send("I have problems using my database, please try again and if the error persists, contact the moderator or developer.")
                print("Problème de lecture du JSON, le fichier est inexistant ou vide ?")
    except FileNotFoundError:
        await ctx.send("I have problems using my database, please try again and if the error persists, contact the moderator or developer.")

    else:
        channel_id = str(ctx.message.channel.id)
        if channel_id in notification_subscribers_dict:
            try:
                notification_subscribers_dict[channel_id].remove(region)
            except ValueError:
                await ctx.send("You were not subscribed to this region notifications")
            else:
                if not notification_subscribers_dict[channel_id]:
                    del notification_subscribers_dict[channel_id]
                with open(NOTIFICATION_SUBSCRIBERS_JSON, "w") as notification_subscribers_json:
                    json.dump(notification_subscribers_dict, notification_subscribers_json)
                await ctx.send("Region " + region + " removed from your subscriptions.")
        else:
            await ctx.send("You will no longer receive notifications from region " + region + ".")

        print("Dictionnaire après modif. écrit dans le JSON: ", notification_subscribers_dict)

@tasks.loop(seconds=10)
async def notify():
    """"""


@client.event
async def on_ready():
    bot_activity.start()


@client.event
async def on_command_error(ctx, error):
    # emoji = '\N{EYES}'
    # await ctx.add_reaction(emoji)
    await ctx.send(f'Error. Try !help ({error})')


client.run(TOKEN)
