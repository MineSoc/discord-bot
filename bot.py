import os
from typing import Union, Optional
import re

import discord
import discord_components
from discord.abc import Messageable
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions, has_role, NoPrivateMessage, Bot, \
    ExpectedClosingQuoteError, Context

from discord_components import DiscordComponents, ComponentsBot, Button, ActionRow
import json

from proceffects import *

TOKEN = os.getenv('WMCS_DISCORD_TOKEN')


def get_prefix(bot, message: discord.Message):
    return when_mentioned_or("WMCS!")(bot, message)


intents = discord.Intents.default()
intents.reactions = True
intents.members = True

bot = ComponentsBot(command_prefix=get_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')


@has_role("Exec")
@bot.command(name="mcguide")
async def mcguide(ctx):
    print(bot.emojis)
    print(bot.get_guild(633724840330788865).channels)
    guide_components = [ActionRow.from_json(b) for b in (json.loads("""[
    {"type": 1, "components": [
        {"type": 2, "style": 5, "disabled": "false", "label": "Survival", "url": "https://discord.com/channels/633724840330788865/882024666762457118/882024833813188649", "emoji": {"name": "pick", "id": 882526831566291004}}, 
        {"type": 2, "style": 5, "label": "Bedrock", "url": "https://discord.com/channels/633724840330788865/884842296112214077/884842297613774848", "emoji": {"name": "bedrockblock", "id": 884818408036765756}}
    ]}, {"type": 1, "components": [
        {"type": 2, "style": 5, "label": "UHC", "url": "https://discord.com/channels/633724840330788865/882025373179731978/882025374463168522", "emoji": {"name": "apple", "id": 651235805951557633}}, 
        {"type": 2, "style": 5, "label": "RftW", "url": "https://discord.com/channels/633724840330788865/882025787690201148/882025789346947082", "emoji": {"name": "wool", "id": 884818265598201917}}, 
        {"type": 2, "style": 5, "label": "Bedwars", "url": "https://discord.com/channels/633724840330788865/882025941197520926/882025942350979084", "emoji": {"name": "bed", "id": 884816256077824042}}

    ]}]"""))]

    await ctx.send("""_ _
<:sqwave2:880600411009060874> **WELCOME TO WARWICK MINECRAFT SOCIETY!** <:sqwave:655468091341406233>
We run both a survival server and frequent events:
Our **survival server** has recently moved to a new spawn! Read more in the link below.
Connect with `warwickmc.uk`, *or `proxy.warwickmc.uk` if on campus.*

Over the summer, we are running **fortnightly events on Thursdays at 7:30pm**. These typically consist of (speed) UHCs and a variety of minigames - with more larger gamemodes coming soon! Read about the gamemodes in use above!

Everything is currently running on Java 1.17.1. Bedrock crossplay/servers is partially implemented, though dedicated bedrock servers are unlikely. Get the role in <#692132927068307486> to be notified of Bedrock news!

Check <#717026685383475330> for the server rules and the links below for information on our servers and <#699591152294297621> for our current execs!
Get your pronoun and fresher roles in <#692132927068307486> and introduce yourself in <#877927457880162304>!

**Next event: Hypixel minigames on Thursday 23rd Sept at 7:30pm**
_ _
**Server Guides**""", components=guide_components)


@has_role("Exec")
@bot.command(name="msg", help="Posts a blank message by this bot, to edit")
async def msg(ctx):
    await ctx.send("_ _")


def get_gcm(url: str):
    # https://discord.com/channels/633724840330788865/867386809688391720/876095725816135710
    g = re.search(r"(https?://)?(www.)?discord.com/channels/(\d+)/(\d+)/(\d+)", url)
    return int(g.group(3)), int(g.group(4)), int(g.group(5))


@bot.event
async def on_error(ctx, err, *args, **kwargs):
    if err == "on_command_error":
        await args[0].send("Something went wrong")
    raise


@bot.event
async def on_command_error(ctx, error: Exception):
    await ctx.message.add_reaction("🚫")
    if isinstance(error, CommandNotFound):
        pass
    elif isinstance(error, NoPrivateMessage):
        await ctx.send("Cannot run this command in DMs")
    elif isinstance(error, ExpectedClosingQuoteError):
        await ctx.send(f"Mismatching quotes, {str(error)}")
    elif hasattr(error, "original"):
        await ctx.send(f"{error}")
        raise error.original
    else:
        await ctx.send(f"{error}")
        raise error


if __name__ == '__main__':
    bot.load_extension("reaction_roles")
    bot.run(TOKEN)
