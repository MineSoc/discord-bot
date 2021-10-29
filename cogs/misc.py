import logging
from discord.ext import commands
from discord.ext.commands import Cog, command

class Misc(Cog):
    """Misc commands"""
    bot: commands.Bot

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        logging.info(f"Misc loaded.")

    @command()
    async def ping(self, ctx):
        """
        Checks bot is responding

        **Example:**
        ```WMCS!ping```
        """
        await ctx.send(f"🏓 Pong!\nLatency: {round(self.bot.latency * 1000)}ms")

    # TODO Welcome message + assign ping party
    # @Cog.listener
    # async def on_member_join(self, member):
    #     await member.send("hello")



def setup(bot):
    bot.add_cog(Misc(bot))