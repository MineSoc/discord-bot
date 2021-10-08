import os
from typing import Union, Optional
import re

import discord
import discord_components
from discord.abc import Messageable
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions, has_role, NoPrivateMessage, Bot, \
    ExpectedClosingQuoteError, Context, Cog, command

from discord_components import DiscordComponents, ComponentsBot, Button, ActionRow
import json

from proceffects import *

import json

from discord_components import ComponentsBot


def from_json(j):
    if isinstance(j, list):
        return [from_json(i) for i in j]
    else:
        return discord_components._get_component_type(j["type"]).from_json(j)


def get_gcm(url: str):
    # https://discord.com/channels/633724840330788865/867386809688391720/876095725816135710
    g = re.search(r"(https?://)?(www.)?discord.com/channels/(\d+)/(\d+)/(\d+)", url)
    return int(g.group(3)), int(g.group(4)), int(g.group(5))




class MsgEdit(Cog):
    bot: ComponentsBot

    def __init__(self, bot):
        self.bot = bot


    @Cog.listener()
    async def on_ready(self):
        print(f"MsgEdit ready.")

    def remove_placeholders(self, ctx: Context, string):
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
            print(match)
            if match.group(1):
                e: discord.Emoji = discord.utils.get(guild.emojis, name=match.group(1))
                if e is None: e = discord.utils.get(self.bot.emojis, name=match.group(1))
                if e is not None: return str(e)
                else: return match.string
        string = re.sub(":([_a-zA-Z]+):", emotes, string)

        return string

    async def edit(self, ctx: Context, url: str, content: Optional[str], embed: Optional[discord.Embed], components: Optional[list[Union[Button, ActionRow]]]):
        kwargs = {}
        if content is not None:
            content = self.remove_placeholders(ctx, content)
            kwargs["content"] = content
        if embed is not None:
            print(embed, embed.title)
            embed.title = self.remove_placeholders(ctx, embed.title)
            embed.description = self.remove_placeholders(ctx, embed.description)
            embed._fields = [{"inline": f["inline"], "name": self.remove_placeholders(ctx, f["name"]), "value": self.remove_placeholders(ctx, f["value"])} for f in embed._fields]
            kwargs["embed"] = embed
        if components is not None: kwargs["components"] = components
    
        gid, cid, mid = get_gcm(url)
        channel: Messageable = ctx.guild.get_channel(cid)
        msg: discord.Message = await channel.fetch_message(mid)
        await msg.edit(**kwargs)
    
    
    @has_role("Exec")
    @command(name="setmsg", help="Edit the text contents")
    @done_react
    async def setmsg(self, ctx: Context, url: str, content: str):
        await self.edit(ctx, url, content, None, None)
    
    
    @has_role("Exec")
    @command(name="setembed")
    @done_react
    async def setembed(self, ctx: Context, url: str, *, embed: str):
        await self.edit(ctx, url, None, discord.Embed.from_dict(json.loads(embed)), None)
    
    
    @has_role("Exec")
    @command(name="setbuttons")
    @done_react
    async def setbuttons(self, ctx: Context, url: str, compMsgID):
        msg: discord.Message = await ctx.fetch_message(compMsgID)
        raw = msg.content
        raw = re.sub(r"^[`a-zA-Z \n]*([\[{])", r"\g<1>", raw)
        raw = re.sub(r"([}\]])[`a-zA-Z \n]*$", r"\g<1>", raw)
        raw = re.sub("`", "\"", raw)
        await self.edit(ctx, url, None, None, from_json(json.loads(raw)))

def setup(bot):
    bot.add_cog(MsgEdit(bot))