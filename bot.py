import os

import discord
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions, has_role, NoPrivateMessage, Bot, \
    ExpectedClosingQuoteError

from discord_components import DiscordComponents, ComponentsBot, Button

TOKEN = os.getenv('WMCS_DISCORD_TOKEN')


def get_prefix(bot, message: discord.Message):
    return when_mentioned_or("WMCS!")(bot, message)


bot = ComponentsBot(command_prefix=get_prefix)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')


@has_role("Exec")
@bot.command(name="mcguide")
async def mcguide(ctx):
    await ctx.send(
        "**Server Guides**",
        components=[
            [
                Button(label="Survival", style=5, url="https://discord.com/channels/633724840330788865/882024666762457118/882024833813188649")
            ],
            [
                Button(label="UHC", style=5, url="https://discord.com/channels/633724840330788865/882025373179731978/882025374463168522"),
                Button(label="RftW", style=5, url="https://discord.com/channels/633724840330788865/882025787690201148/882025789346947082"),
                Button(label="Bedwars", style=5, url="https://discord.com/channels/633724840330788865/882025941197520926/882025942350979084")
            ]
        ],
    )


@bot.event
async def on_error(ctx, err, *args, **kwargs):
    if err == "on_command_error":
        await args[0].send("Something went wrong")
    raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        pass
    elif isinstance(error, NoPrivateMessage):
        await ctx.send("Cannot run this command in DMs")
    elif isinstance(error, ExpectedClosingQuoteError):
        await ctx.send(f"Mismatching quotes, {str(error)}")
    elif hasattr(error, "original"):
        raise error.original
    else: raise error

bot.run(TOKEN)
