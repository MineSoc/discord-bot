import asyncio
import functools

from discord.ext.commands import Context


def wait_react(func):
    """
    Reacts to the command message with a clock while message processing is ongoing
    Most useful on commands with longer processing times
    """
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await ctx.message.add_reaction("🕐")
        await func(*args, **kwargs)
        await ctx.message.remove_reaction("🕐", ctx.me)
    return decorator


def done_react(func):
    """
    Reacts to the command message with a thumbs up once command processing is complete
    Most useful on commands with no direct result message
    """
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await func(*args, **kwargs)
        await ctx.message.add_reaction("👍")
    return decorator


def remove_command(time=0):
    """Removes the command message after time seconds"""
    def decorator_outer(func):
        @functools.wraps(func)
        async def decorator(*args, **kwargs):
            # Find context in arguments - probably 1st, but not 100%
            ctx: Context = next(a for a in args if isinstance(a, Context))
            await func(*args, **kwargs)
            await asyncio.sleep(time)
            await ctx.message.delete()
        return decorator
    return decorator_outer
