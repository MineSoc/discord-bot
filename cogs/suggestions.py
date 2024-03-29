import asyncio
import logging

import discord
from discord import Thread
from discord.ext import commands
from discord.ext.commands import Bot, Context, Cog, command, bot_has_permissions, guild_only

from utils import utils


class Suggestions(Cog):
    """Organises suggestions in #suggestions"""

    bot: Bot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        logging.info(f"Suggestions loaded.")

    # Checks bot has these perms in #suggestions and #exec-suggestions
    channel_converter = utils.BotHasPermsInChannel(view_channel=True, send_messages=True, embed_links=True, add_reactions=True, create_public_threads=True)

    @command()
    @bot_has_permissions(send_messages=True, add_reactions=True, embed_links=True, create_public_threads=True)
    @guild_only()
    async def suggest(self, ctx: Context, title, *, suggestion=""):
        """
        Creates a suggestion with a discussion thread

        **Example:**
        ```WMCS!suggest "Suggestions Bot" Add a bot to organize suggestions```
        """
        orig_title = title
        title = "Suggestion | " + orig_title

        guild: discord.Guild = ctx.guild
        # noinspection PyTypeChecker
        channel: discord.TextChannel = await self.channel_converter.convert(ctx, "suggestions")

        embed = self.create_embed(ctx, title, suggestion)
        msg = await self.post_suggestion(channel, embed, title)

        try:
            # noinspection PyTypeChecker
            channel: discord.TextChannel = await self.channel_converter.convert(ctx, "exec-suggestions")
        except utils.BotMissingPermissionsChannel as e:
            logging.info(f"{ctx.guild.name}: {e}")
            return
        if not channel: return
        title = "Exec Discussion | " + orig_title
        embed = self.create_embed(ctx, title, suggestion, msg)
        await self.post_suggestion(channel, embed, title)


    @staticmethod
    def create_embed(ctx, title, suggestion, orig_message: discord.Message = None):
        embed: discord.Embed = discord.Embed()
        embed.title = title
        embed.description = suggestion
        if orig_message is not None:
            embed.url = orig_message.jump_url
        embed.set_author(name=ctx.author.display_name, url=ctx.message.jump_url, icon_url=ctx.author.avatar.url)
        return embed


    @staticmethod
    async def post_suggestion(channel, embed, thread_name):
        message: discord.Message = await channel.send(embed=embed)
        await channel.create_thread(name=thread_name, message=message)
        # Add vote reactions
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        return message



    @command()
    @commands.has_role("Exec")
    async def approve(self, ctx: Context, msg: discord.Message, *, reason: str = ""):
        """
        Approves a suggestion.

        **Example:**
        ```WMCS!approve <msg link> Has been needed for a while```
        """
        await self.suggestion_action(ctx, msg, "✅", "Suggestion Approved", reason)


    @command()
    @commands.has_role("Exec")
    async def deny(self, ctx: Context, msg: discord.Message, *, reason: str = ""):
        """
        Denies a suggestion.

        **Example:**
        ```WMCS!deny <msg link> Very bad idea```
        """
        await self.suggestion_action(ctx, msg, "❌", "Suggestion Denied", reason)


    async def suggestion_action(self, ctx, msg, emoji, action, reason):
        if reason: text = f"{emoji} **{action}**\n{reason}"
        else: text = f"{emoji} **{action}**"

        await msg.clear_reactions()
        await msg.add_reaction(emoji)
        thread: Thread = next(t for t in msg.channel.threads if t.id == msg.id)
        if thread is None: return
        await thread.send(text)

def setup(bot):
    bot.add_cog(Suggestions(bot))
