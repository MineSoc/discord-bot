import os

import discord
from discord.ext.commands import when_mentioned_or, CommandNotFound, NoPrivateMessage, ExpectedClosingQuoteError
from discord_components import ComponentsBot

from utils.proceffects import *

# List of accepted prefixes
PREFIXES = ["WMCS!"]
# Fetch token from env
TOKEN = os.getenv('WMCS_DISCORD_TOKEN')
# TODO Check Version Number
VERSION = "1.3.0-d.2"


intents = discord.Intents.default()
intents.members = True

bot = ComponentsBot(command_prefix=lambda bot, msg: when_mentioned_or(*PREFIXES)(bot, msg), intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')


@bot.command(help="Check bot is working")
@remove_command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong!\nLatency: {round(bot.latency * 1000)}ms")


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


# Load cogs and run
if __name__ == '__main__':
    bot.load_extension("reaction_roles")
    bot.load_extension("msg_edit")
    bot.load_extension("betterhelp")
    bot.run(TOKEN)
