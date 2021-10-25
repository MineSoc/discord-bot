import os
import logging
import sys

import discord
from discord import Forbidden
from discord.ext.commands import when_mentioned_or
from discord.ext.commands.errors import *
from discord_components import ComponentsBot

import utils.utils
from utils.proceffects import *
from utils.pretty_help import DefaultMenu, PrettyHelp

# List of accepted prefixes
PREFIXES = ["WMCS!"]
# Fetch token from env
TOKEN = os.getenv('WMCS_DISCORD_TOKEN')
# TODO Check Version Number
VERSION = "1.3.3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(funcName)s:%(lineno)d [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("discord.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

intents = discord.Intents.default()
intents.members = True

bot = ComponentsBot(command_prefix=lambda bot, msg: when_mentioned_or(*PREFIXES)(bot, msg), intents=intents)
bot.help_command = PrettyHelp(no_category="Misc")

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord')


@bot.event
async def on_error(ctx, err, *args, **kwargs):
    if err == "on_command_error":
        await args[0].send("Something went wrong")
    raise


async def error_delete(msg: discord.Message, r):
    await msg.delete()


@bot.event
async def on_command_error(ctx: Context, error: Exception):
    # await ctx.message.add_reaction("🚫")
    message = ""
    reraise = None
    # Custom discord parsing error messages
    if isinstance(error, CommandNotFound):
        pass
    elif isinstance(error, NoPrivateMessage):
        message = "Cannot run this command in DMs"
    elif isinstance(error, ExpectedClosingQuoteError):
        message = f"Mismatching quotes, {str(error)}"
    elif isinstance(error, MissingRequiredArgument):
        message = f"Argument {str(error.param.name)} is missing\nUsage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`"
    elif isinstance(error, Forbidden):
        message = f"Bot does not have permissions to do this. {str(error.text)}"
        reraise = error
    elif hasattr(error, "original"):
        await on_command_error(ctx, error.original)
        return
    elif isinstance(error, CommandError):
        message = str(error)
    else:
        message = f"{error}"
        reraise = error
    if reraise: logging.error(reraise, exc_info=True)

    # if message: await ctx.send(message)
    if message: await utils.utils.confirmation(ctx, "", "", ["🚫"], error_delete, utils.utils.nothing, content=message)
    if reraise: raise reraise


# Load cogs and run
if __name__ == '__main__':
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'): bot.load_extension(f'cogs.{filename[:-3]}')

    bot.run(TOKEN)
