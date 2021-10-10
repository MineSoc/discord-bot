from typing import Optional

import discord
from discord.ext import commands

import bot
from utils.exec_cog import ExecCog

"""
Improved help message, requires "help_command=None" in the Bot definition parameters

Original concept by Jared Newsom (AKA Jared M.F.)
[Deleted] https://gist.github.com/StudioMFTechnologies/ad41bfd32b2379ccffe90b0e34128b8b
Based on rewrite by by github.com/nonchris
https://gist.github.com/nonchris/1c7060a14a9d94e7929aa2ef14c41bc2
"""


class Help(commands.Cog):
    """Sends this help message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, module: Optional[str]):
        """Lists all modules of the bot"""

        prefix = bot.PREFIXES[0]
        version = bot.VERSION
        author = "EricTheLemur#8899"

        # If no module specified, list all
        if not module:
            exec_mods = discord.utils.get(ctx.guild.roles, name="Exec") in ctx.author.roles
            emb = discord.Embed(title='__Commands and Modules__', color=discord.Color.blue(),
                                description=f'Use `{prefix}help <module>` to gain more information about a module\n')

            # adding cogs to modules embed
            cogs_desc = ''
            for name, cog in self.bot.cogs.items():
                if name == self.__class__.__name__: continue
                print(name, exec_mods, isinstance(cog, ExecCog))
                if not exec_mods and isinstance(cog, ExecCog): continue
                cogs_desc += f'`{name}` {cog.__doc__}\n'

            emb.add_field(name='__Modules__', value=cogs_desc, inline=False)

            # adding uncategorized commands
            commands_desc = ''
            commands_desc += f'`help` - Sends this help message\n'
            for command in self.bot.walk_commands():
                # list if not cog cmd or hidden
                if not command.cog_name and not command.hidden:
                    commands_desc += f'`{command.name}` - {command.help}\n'

            # adding those commands to embed
            if commands_desc: emb.add_field(name='Misc Commands', value=commands_desc, inline=False)

            emb.set_footer(text=f"Bot by {author} | Version {version}")
            await ctx.send(embed=emb)

        # if cog name given
        else:
            # Find cog
            for cog in self.bot.cogs:
                if cog.lower() == module.lower():

                    # making title - getting description from doc-string of class
                    emb = discord.Embed(title=f'__{cog} Commands__', description="__" + self.bot.cogs[cog].__doc__ + "__",
                                        color=discord.Color.green())

                    # getting commands from cog
                    for command in self.bot.get_cog(cog).get_commands():
                        if not command.hidden:
                            emb.add_field(name=f"`{prefix}{command.name}`", value=command.help, inline=False)

                    await ctx.send(embed=emb)
                    # found cog - breaking loop
                    break

            # if input not found (no break called)
            else:
                await ctx.send(f"No module named {module} exists.")
                return


def setup(bot):
    bot.add_cog(Help(bot))
