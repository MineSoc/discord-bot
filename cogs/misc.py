from discord.ext.commands import Cog, command

class Misc(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f"Misc loaded.")

    @command()
    async def ping(self, ctx):
        """
        Checks bot is responding

        **Example:**
        ```WMCS!ping```
        """
        await ctx.send(f"🏓 Pong!\nLatency: {round(self.bot.latency * 1000)}ms")


def setup(bot):
    bot.add_cog(Misc(bot))