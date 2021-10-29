import json
import logging
import re
from typing import Optional

import discord
import discord_components
from discord.ext.commands import Cog, command
from discord_components import ComponentsBot

from utils.exec_cog import ExecCog
from utils.proceffects import *

from utils.utils import *


class MsgEdit(ExecCog):
    """Post and edit bot messages, embeds and buttons - @Exec only"""

    bot: ComponentsBot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        logging.info(f"MsgEdit loaded.")

    @command()
    async def msg(self, ctx):
        """Posts a blank message by this bot, to edit"""
        await ctx.send("_ _")


    @command()
    @done_react
    async def setmsg(self, ctx: Context, target_url: discord.Message, *, content):
        """
        Edits the text of a bot message.

        This bot must be the author of the message.

        **Example:**
        ```WMCS!setmsg https://discord.com/channels/633724840330788865/649312564064419921/897509447205797908 New message contents```
        """

        await self.edit(ctx, target_url, content, None, None)

    @command()
    @done_react
    async def setembed(self, ctx: Context, target_url: discord.Message, *, embed: str):
        """
        Edits the embed of a bot message.

        This bot must be the author of the message. At minimum, attributes title, description and fields should be provided.

        **Example:**
        ```WMCS!setembed https://discord.com/channels/633724840330788865/649352839788888075/649355020092964893 {
            "title": "Example",
            "description": "Example Embed",
            "fields": []
        }```
        """
        embed = discord.Embed.from_dict(json.loads(embed))
        await self.edit(ctx, target_url, None, embed, None)

    @command()
    @done_react
    async def setbuttons(self, ctx: Context, target_url: discord.Message, *, buttons: str):
        """
        Edit the buttons of a bot message.

        This bot must be the author of the message.

        **Example:**
        ```WMCS!setbuttons https://discord.com/channels/633724840330788865/649352839788888075/649355020092964893 <button data>```
        """

        raw = buttons
        raw = re.sub(r"^[`a-zA-Z \n]*([\[{])", r"\g<1>", raw)
        raw = re.sub(r"([}\]])[`a-zA-Z \n]*$", r"\g<1>", raw)
        raw = re.sub("`", "\"", raw)
        button_objs = self.buttons_from_json(json.loads(raw))

        await self.edit(ctx, target_url, None, None, button_objs)


    @command()
    async def get_msg(self, ctx: Context, url: str):
        """Get the raw contents of a message

        Currently unimplemented.
        """
        raise NotImplementedError()


    @command()
    async def copy_msg(self, ctx: Context, target_channel: discord.TextChannel, src_msg: discord.Message):
        """
        Posts a copy of a message to the given channel.

        **Example:**
        ```WMCS!setbuttons https://discord.com/channels/633724840330788865/649352839788888075/649355020092964893 <button data>```
        """

        # noinspection PyArgumentList
        await target_channel.send(content=src_msg.content, embeds=src_msg.embeds, components=src_msg.components)

    # TODO Copy content/embed/button


    async def edit(self, ctx: Context, msg: discord.Message, content: Optional[str], embed: Optional[discord.Embed], components):
        """Base edit message"""
        kwargs = {}
        if content is not None:  # Remove placeholders from message
            content = self.remove_placeholders(ctx, content)
            kwargs["content"] = content
        if embed is not None:  # Remove placeholders from embed
            embed.title = self.remove_placeholders(ctx, embed.title)
            embed.description = self.remove_placeholders(ctx, embed.description)
            embed._fields = [{"inline": f["inline"], "name": self.remove_placeholders(ctx, f["name"]),
                              "value": self.remove_placeholders(ctx, f["value"])} for f in embed._fields]
            kwargs["embed"] = embed
        if components is not None: kwargs["components"] = components

        await msg.edit(**kwargs)

    @staticmethod
    def remove_placeholders(ctx: Context, string):
        """Replaces channel, user, role and emote placeholders"""
        guild: discord.Guild = ctx.guild

        # def channel(match: re.Match):
        #     print(match)
        #     if match.group(1):
        #         c: discord.TextChannel = discord.utils.get(guild.channels, name=match.group(1))
        #         if c is not None: return f"<#{c.id}>"
        #         else: return match.string
        # string = re.sub("#([a-z-]+)", channel, string)
        #
        # def user(match: re.Match):
        #     print(match)
        #     if match.group(1):
        #         u: discord.User = discord.utils.get(guild.members, name=match.group(1))
        #         if u is not None: return f"<@{u.id}>"
        #         else: return match.string
        # string = re.sub("@([^@#\w]+#\d\d\d\d)", user, string)
        #
        # def roles(match: re.Match):
        #     print(match)
        #     if match.group(1):
        #         r: discord.Role = discord.utils.get(guild.roles, name=match.group(1))
        #         if r is not None: return f"<@&{r.id}>"
        #         else: return match.string
        # string = re.sub("@([^@#\w]+)", roles, string)

        def emotes(match: re.Match):
            if match.group(2):
                e: discord.Emoji = discord.utils.get(guild.emojis, name=match.group(2))
                if e is None: e = discord.utils.get(ctx.bot.emojis, name=match.group(2))
                if e is not None: return match.group(1) + str(e)
            return match.group(0)

        string = re.sub("([^<]|^):([-_a-zA-Z0-9]+):", emotes, string)

        return string

    @staticmethod
    def buttons_from_json(j):
        """Gets button data from raw JSON"""
        if isinstance(j, list): return [MsgEdit.buttons_from_json(i) for i in j]
        else: return discord_components._get_component_type(j["type"]).from_json(j)



def setup(bot):
    bot.add_cog(MsgEdit(bot))



#
# @has_role("Exec")
# @bot.command(name="mcguide")
# async def mcguide(ctx):
#     print(bot.emojis)
#     print(bot.get_guild(633724840330788865).channels)
#     guide_components = [ActionRow.from_json(b) for b in (json.loads("""[
#     {"type": 1, "components": [
#         {"type": 2, "style": 5, "disabled": "false", "label": "Survival", "url": "https://discord.com/channels/633724840330788865/882024666762457118/882024833813188649", "emoji": {"name": "pick", "id": 882526831566291004}},
#         {"type": 2, "style": 5, "label": "Bedrock", "url": "https://discord.com/channels/633724840330788865/884842296112214077/884842297613774848", "emoji": {"name": "bedrockblock", "id": 884818408036765756}}
#     ]}, {"type": 1, "components": [
#         {"type": 2, "style": 5, "label": "UHC", "url": "https://discord.com/channels/633724840330788865/882025373179731978/882025374463168522", "emoji": {"name": "apple", "id": 651235805951557633}},
#         {"type": 2, "style": 5, "label": "RftW", "url": "https://discord.com/channels/633724840330788865/882025787690201148/882025789346947082", "emoji": {"name": "wool", "id": 884818265598201917}},
#         {"type": 2, "style": 5, "label": "Bedwars", "url": "https://discord.com/channels/633724840330788865/882025941197520926/882025942350979084", "emoji": {"name": "bed", "id": 884816256077824042}}
#
#     ]}]"""))]
#
#     await ctx.send("""_ _
# <:sqwave2:880600411009060874> **WELCOME TO WARWICK MINECRAFT SOCIETY!** <:sqwave:655468091341406233>
# We run both a survival server and frequent events:
# Our **survival server** has recently moved to a new spawn! Read more in the link below.
# Connect with `warwickmc.uk`, *or `proxy.warwickmc.uk` if on campus.*
#
# Over the summer, we are running **fortnightly events on Thursdays at 7:30pm**. These typically consist of (speed) UHCs and a variety of minigames - with more larger gamemodes coming soon! Read about the gamemodes in use above!
#
# Everything is currently running on Java 1.17.1. Bedrock crossplay/servers is partially implemented, though dedicated bedrock servers are unlikely. Get the role in <#692132927068307486> to be notified of Bedrock news!
#
# Check <#717026685383475330> for the server rules and the links below for information on our servers and <#699591152294297621> for our current execs!
# Get your pronoun and fresher roles in <#692132927068307486> and introduce yourself in <#877927457880162304>!
#
# **Next event: Hypixel minigames on Thursday 23rd Sept at 7:30pm**
# _ _
# **Server Guides**""", components=guide_components)
