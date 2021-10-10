import json
import re
from typing import Union, Optional

import discord
import discord_components
from discord.abc import Messageable
from discord.ext.commands import Cog, command
from discord_components import Button, ActionRow
from discord_components import ComponentsBot

from utils.exec_cog import ExecCog
from utils.proceffects import *


class MsgEdit(ExecCog):
    """Post and edit bot messages, embeds and buttons"""

    bot: ComponentsBot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f"MsgEdit ready.")

    @command(name="msg", help="Posts a blank message by this bot, to edit")
    async def msg(self, ctx):
        await ctx.send("_ _")


    @command(help="Edit the text of the message")
    @done_react
    async def setmsg(self, ctx: Context, url: str, content: str):
        await self.edit(ctx, url, content, None, None)

    @command(help="Edit the embeds of the message")
    @done_react
    async def setembed(self, ctx: Context, url: str, *, embed: str):
        await self.edit(ctx, url, None, discord.Embed.from_dict(json.loads(embed)), None)

    @command(help="Edit the buttons of the message")
    @done_react
    async def setbuttons(self, ctx: Context, url: str, button_msg_id):
        msg: discord.Message = await ctx.fetch_message(button_msg_id)
        raw = msg.content
        raw = re.sub(r"^[`a-zA-Z \n]*([\[{])", r"\g<1>", raw)
        raw = re.sub(r"([}\]])[`a-zA-Z \n]*$", r"\g<1>", raw)
        raw = re.sub("`", "\"", raw)
        await self.edit(ctx, url, None, None, self.buttons_from_json(json.loads(raw)))


    async def edit(self, ctx: Context, url: str, content: Optional[str], embed: Optional[discord.Embed],
                   components: Optional[list[Union[Button, ActionRow]]]):
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

        # Fetch then edit message
        gid, cid, mid = self.get_gcm(url)
        channel: Messageable = ctx.guild.get_channel(cid)
        msg: discord.Message = await channel.fetch_message(mid)
        await msg.edit(**kwargs)

    def remove_placeholders(self, ctx: Context, string):
        """Replaces channel, user, role and emote placeholders"""
        guild: discord.Guild = ctx.guild
        print(string)

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
            if match.group(1):
                e: discord.Emoji = discord.utils.get(guild.emojis, name=match.group(1))
                if e is None: e = discord.utils.get(self.bot.emojis, name=match.group(1))
                if e is not None: return str(e)
                else: return match.string

        string = re.sub(":([_a-zA-Z]+):", emotes, string)

        return string

    @staticmethod
    def buttons_from_json(j):
        """Gets button data from raw JSON"""
        if isinstance(j, list): return [MsgEdit.buttons_from_json(i) for i in j]
        else: return discord_components._get_component_type(j["type"]).from_json(j)

    @staticmethod
    def get_gcm(url: str):
        """Gets guild id, channel id and message id from link"""
        g = re.search(r"(https?://)?(www.)?discord.com/channels/(\d+)/(\d+)/(\d+)", url)
        return int(g.group(3)), int(g.group(4)), int(g.group(5))


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
