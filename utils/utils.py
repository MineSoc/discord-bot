import re
import discord
from discord.abc import Messageable
from discord.ext.commands import Context

from asyncio.exceptions import TimeoutError


# Message handling
def get_gcm(url: str):
    """Gets guild id, channel id and message id from link"""
    g = re.search(r"(https?://)?(www.)?discord.com/channels/(\d+)/(\d+)/(\d+)", url)
    return int(g.group(3)), int(g.group(4)), int(g.group(5))


async def get_msg_from_link(ctx, url):
    """Fetches a message from a link"""
    gid, cid, mid = get_gcm(url)
    channel: Messageable = ctx.guild.get_channel(cid)
    msg: discord.Message = await channel.fetch_message(mid)
    return msg


async def confirmation(ctx: Context, title: str, body: str, reactions, confirm_func, reject_func, timeout=60, fields=None):
    """
    Posts an embed with the prompt.
    If the author reacts with one of reactions before timeout, confirm_func will be called.
    Otherwise, reject_func will be called
    """
    embed = discord.Embed(title=title, description=body)
    if fields:
        for f in fields:
            if isinstance(f, dict): embed.add_field(**f)
            if isinstance(f, list) or isinstance(f, tuple): embed.add_field(name=f[0], value=f[1], inline=False)

    msg: discord.Message = await ctx.send(embed=embed)
    for em in reactions:
        await msg.add_reaction(em)

    try:
        r, _ = await ctx.bot.wait_for("reaction_add",
                      check=lambda r, u: r.message.id == msg.id and u == ctx.message.author and str(r.emoji) in reactions,
                      timeout=timeout)
        await confirm_func(msg, r)
    except TimeoutError:
        await reject_func(msg)
