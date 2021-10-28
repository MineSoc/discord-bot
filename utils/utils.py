import discord
from discord.ext import commands
from discord.ext.commands import Context

from asyncio.exceptions import TimeoutError


async def nothing(*args):
    pass


# Check bot perms in channel argument
class BotHasPermsInChannel(commands.TextChannelConverter):
    def __init__(self, **perms):
        invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
        if invalid:
            raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
        self.perms = perms

    async def convert(self, ctx: Context, argument: str) -> discord.TextChannel:
        channel = await super().convert(ctx, argument)
        # From commands.bot_has_permissions
        me = channel.guild.me if channel.guild is not None else ctx.bot.user
        permissions = channel.permissions_for(me)

        missing = [perm for perm, value in self.perms.items() if getattr(permissions, perm) != value]
        if not missing: return channel
        raise BotMissingPermissionsChannel(channel, missing)


# Check bot perms in channel argument
class ExternalEmoji(commands.EmojiConverter):
    async def convert(self, ctx: Context, argument: str) -> discord.Emoji:
        try:
            emoji = await super().convert(ctx, argument)
        except commands.BadArgument:
            emoji = discord.utils.get(ctx.bot.emojis, name=argument.strip(": "))

        if emoji: return emoji
        raise commands.errors.BadArgument(f"{argument} is an invalid emoji.")


class BotMissingPermissionsChannel(commands.BotMissingPermissions):
    def __init__(self, channel: discord.TextChannel, missing_permissions, *args):
        # From BotMissingPermissions
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]

        if len(missing) > 2: fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else: fmt = ' and '.join(missing)
        message = f'Bot requires {fmt} permission(s) in {channel.mention} to run this command.'

        super(commands.BotMissingPermissions, self).__init__(message, *args)


class NoSuchArgumentExists(Exception):
    def __init__(self, arg: str):
        super().__init__(f"Argument {arg} does not exist.")


# Confirm messages
async def confirmation(ctx: Context, title: str, body: str, reactions, confirm_func, reject_func, timeout=60, content="", fields=None):
    """
    Posts an embed with the prompt.
    If the author reacts with one of reactions before timeout, confirm_func will be called.
    Otherwise, reject_func will be called
    """
    kwargs = {}
    if title or body:
        embed = discord.Embed(title=title, description=body)
        if fields:
            for f in fields:
                if isinstance(f, dict): embed.add_field(**f)
                if isinstance(f, list) or isinstance(f, tuple): embed.add_field(name=f[0], value=f[1], inline=False)
        kwargs["embed"] = embed
    if content: kwargs["content"] = content

    msg: discord.Message = await ctx.send(**kwargs)
    for em in reactions:
        await msg.add_reaction(em)

    try:
        r, _ = await ctx.bot.wait_for("reaction_add",
                      check=lambda r, u: r.message.id == msg.id and u == ctx.message.author and str(r.emoji) in reactions,
                      timeout=timeout)
        await confirm_func(msg, r)
    except TimeoutError:
        await reject_func(msg)
