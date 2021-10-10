import discord
from discord.ext.commands import Bot, Context, Cog, command

from utils.proceffects import remove_command


class Suggestions(Cog):
    """Organises suggestions in #suggestions"""

    bot: Bot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f"Suggestions ready.")


    @command(help="Create a suggestion")
    @remove_command(5)
    async def suggest(self, ctx: Context, title, *, suggestion=""):
        title = "Suggestion | " + title

        guild: discord.Guild = ctx.guild
        channel: discord.TextChannel = discord.utils.get(guild.channels, name="suggestions")
        author: discord.User = ctx.author

        # Create embed
        embed: discord.Embed = discord.Embed()
        embed.title = title
        embed.description = suggestion
        embed.set_author(name=author.display_name, url=ctx.message.jump_url, icon_url=author.avatar.url)

        # Post message and thread
        message: discord.Message = await channel.send(embed=embed)
        await channel.create_thread(name=title, message=message)
        # Add vote reactions
        await message.add_reaction("👍")
        await message.add_reaction("👎")


def setup(bot):
    bot.add_cog(Suggestions(bot))
