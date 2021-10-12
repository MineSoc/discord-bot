from discord.ext.commands import Cog
from discord.utils import get


class ExecCog(Cog):
    """Limits a Cog to only be usable by those with the @Exec role"""
    async def cog_check(self, ctx):
        if not ctx.guild: return False
        exec = get(ctx.guild.roles, name="Exec")
        result = exec in ctx.author.roles
        return result