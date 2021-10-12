import asyncio

import discord
from discord.ext.commands import Bot, Context, Cog, command



class Suggestions(Cog):
    """Organises suggestions in #suggestions"""

    bot: Bot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f"Suggestions loaded.")


    @command()
    async def suggest(self, ctx: Context, title, *, suggestion=""):
        """
        Creates a suggestion with a discussion thread

        **Example:**
        ```WMCS!suggest "Suggestions Bot" Add a bot to organize suggestions```
        """
        orig_title = title
        title = "Suggestion | " + orig_title

        guild: discord.Guild = ctx.guild
        channel: discord.TextChannel = discord.utils.get(guild.channels, name="suggestions")

        embed = self.create_embed(ctx, title, suggestion)
        msg = await self.post_suggestion(channel, embed, title)

        channel: discord.TextChannel = discord.utils.get(guild.channels, name="exec-suggestions")
        title = "Exec Discussion | " + orig_title
        embed = self.create_embed(ctx, title, suggestion, msg)
        await self.post_suggestion(channel, embed, title)

        if ctx.channel.name == "suggestions":
            await asyncio.sleep(5)
            await ctx.message.delete()


    @staticmethod
    def create_embed(ctx, title, suggestion, orig_message: discord.Message = None):
        embed: discord.Embed = discord.Embed()
        embed.title = title
        embed.description = suggestion
        if orig_message is not None:
            embed.url = orig_message.jump_url
        embed.set_author(name=ctx.author.display_name, url=ctx.message.jump_url, icon_url=ctx.author.avatar.url)
        return embed


    async def post_suggestion(self, channel, embed, thread_name):
        message: discord.Message = await channel.send(embed=embed)
        await channel.create_thread(name=thread_name, message=message)
        # Add vote reactions
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        return message


def setup(bot):
    bot.add_cog(Suggestions(bot))
