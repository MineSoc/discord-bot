import discord
from discord.embeds import EmbedProxy
from discord.ext import commands
import json
import atexit
import uuid

from discord_components import ComponentsBot

reaction_roles_data = {}

# Load or create storage JSON
try:
    with open("reaction_roles.json") as file:
        reaction_roles_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as ex:
    with open("reaction_roles.json", "w") as file:
        json.dump({}, file)

class ReferenceAlreadyExists(Exception):
    def __init__(self, str):
        super().__init__(str)


class NoMessageExists(Exception):
    def __init__(self, str):
        super().__init__(str)

# Store unsaved data on exit
@atexit.register
def store_reaction_roles():
    with open("reaction_roles.json", "w") as file:
        json.dump(reaction_roles_data, file)


class ReactionRoles(commands.Cog):
    bot: ComponentsBot

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"ReactionRoles ready.")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id: return
        # Get role from reaction (if exists)
        role, user = self.parse_reaction_payload(payload)

        if role is not None and user is not None:
            # Toggle role
            if role not in user.roles: await user.add_roles(role, reason="ReactionRole")
            else: await user.remove_roles(role, reason="ReactionRole")

            # Remove reaction
            channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
            message: discord.PartialMessage = channel.get_partial_message(payload.message_id)
            await message.remove_reaction(payload.emoji, user)


    @commands.has_permissions(manage_channels=True)
    @commands.command(help="Create message to add reactions to")
    async def reaction(self, ctx, channel: discord.TextChannel, reference, title, message):
        embed = discord.Embed(title=title, description=message)
        embed.add_field(name="Roles", value="_ _", inline=False)
        msg = await channel.send(embed=embed)
        if not self.add_message(ctx.guild.id, msg, reference):
            await msg.delete()
            raise ReferenceAlreadyExists(f"A reaction message with reference `{reference}` already exists.")


    @commands.has_permissions(manage_channels=True)
    @commands.command(help="Add reaction to reaction message")
    async def reaction_add(self, ctx, msg_reference, emote, role: discord.Role, description=None):
        print(f"Adding role {role.name} for emoji {emote}")
        guild: discord.Guild = ctx.guild
        msg_data = self.get_msg_from_ref(guild.id, msg_reference)
        if not msg_data: raise NoMessageExists(f"No message exists with reference `{msg_reference}`.")
        channel = guild.get_channel(msg_data["channelID"])

        message: discord.Message = await channel.fetch_message(msg_data["messageID"])

        emote = self.get_emoji(ctx, emote)
        print(emote)

        # Edit embed to include new option
        embed: discord.Embed = message.embeds[0]
        field: EmbedProxy = embed.fields[0]
        embed.remove_field(0)

        if field.value == "_ _": field.value = ""
        new_val = field.value + f"\n{emote} {description if description is not None else role.name}"
        embed.add_field(name=field.name, value=new_val)
        await message.edit(embed=embed)

        # Add reaction to list
        self.add_reaction(ctx.guild.id, msg_reference, emote, role.id)
        await message.add_reaction(emote)


    def get_emoji(self, ctx, emote):
        if isinstance(emote, discord.Emoji): return emote
        if isinstance(emote, str):
            if emote[0] == ":" and emote[-1] == ":":
                emote = emote[1:-1]
            guild: discord.Guild = ctx.guild
            result = discord.utils.get(guild.emojis, name=emote)
            if result is not None: return result
            else: return discord.utils.get(self.bot.emojis, name=emote)
        return None



    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def reactions(self, ctx):
        guild_id = ctx.guild.id
        data = reaction_roles_data.get(str(guild_id), None)
        embed = discord.Embed(title="Reaction Roles")
        if data is None:
            embed.description = "There are no reaction roles set up right now."
        else:
            for reference, msg_data in data.items():
                embed.add_field(**self.msg_field(ctx, reference, msg_data))
        await ctx.send(embed=embed)


    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def reaction_remove(self, ctx, reference: str):
        guild: discord.Guild = ctx.guild
        guild_id = ctx.guild.id
        data = reaction_roles_data.get(str(guild_id), None)
        embed = discord.Embed(title=f"Remove Reaction Role {reference}")
        if data is None or data.get(reference) is None:
            raise NoMessageExists(f"No message exists with reference `{reference}`.")

        embed.description = "React with 🗑️ to confirm removal of message " + reference
        msg_data = data[reference]
        embed.add_field(**self.msg_field(ctx, reference, msg_data))

        msg = await ctx.send(embed=embed)
        if msg_data is not None:
            await msg.add_reaction("🗑️")

            await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and u == ctx.message.author and str(r.emoji) == "🗑️", timeout=60)
            channel: discord.TextChannel = guild.get_channel(msg_data["channelID"])
            orig_message: discord.PartialMessage = channel.get_partial_message(msg_data["messageID"])
            await orig_message.delete()
            del data[reference]
            reaction_roles_data[str(guild_id)] = data
            store_reaction_roles()


    def add_message(self, guild_id, message: discord.Message, reference):
        if not str(guild_id) in reaction_roles_data:
            reaction_roles_data[str(guild_id)] = {}

        if reaction_roles_data[str(guild_id)].get(reference):
            return False
        reaction_roles_data[str(guild_id)][reference] = {
            "channelID": message.channel.id,
            "messageID": message.id,
            "roles": {}
        }
        store_reaction_roles()
        return True


    def add_reaction(self, guild_id, reference, emote, role_id):
        reaction_roles_data[str(guild_id)][reference]["roles"][str(emote)] = role_id
        store_reaction_roles()


    def get_msg_from_ids(self, guild_id, channel_id, message_id):
        data = reaction_roles_data.get(str(guild_id), None)
        if data is not None:
            for ref, msg in data.items():
                if channel_id == msg.get("channelID") and message_id == msg.get("messageID"):
                    return ref, msg
        return None, None

    def get_msg_from_ref(self, guild_id, reference):
        data = reaction_roles_data.get(str(guild_id), None)
        if data is not None:
            msg_data = data.get(reference)
            return msg_data

    def msg_field(self, ctx, reference, msg_data):
        channel_id = msg_data.get("channelID")
        message_id = msg_data.get("messageID")
        field_title = str(reference)
        field_value = f"[message](https://www.discordapp.com/channels/{ctx.guild.id}/{channel_id}/{message_id})"
        for emote, role_id in msg_data["roles"].items():
            field_value += f"\n{emote} {ctx.guild.get_role(role_id)}"
        return {"name": field_title, "value": field_value, "inline": False}

    def parse_reaction_payload(self, payload: discord.RawReactionActionEvent):
        guild_id = payload.guild_id
        ref, msg_data = self.get_msg_from_ids(payload.guild_id, payload.channel_id, payload.message_id)
        if ref is not None and msg_data is not None:
            guild: discord.Guild = self.bot.get_guild(guild_id)
            role = guild.get_role(msg_data["roles"].get(str(payload.emoji)))
            user = guild.get_member(payload.user_id)

            return role, user
        return None, None


def setup(bot):
    bot.add_cog(ReactionRoles(bot))