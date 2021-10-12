import discord
from discord.ext import commands
from discord_components import ComponentsBot

from utils.exec_cog import ExecCog
from utils.json_storage import JSONStorage

REACTION_ROLES_FILE = "reaction_roles.json"


class ReactionRoles(JSONStorage, ExecCog):
    """Toggle roles with reactions in #get-roles - @Exec only"""

    bot: ComponentsBot

    def __init__(self, bot):
        super(ReactionRoles, self).__init__(REACTION_ROLES_FILE)
        self.bot = bot
        print(self.data)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"ReactionRoles loaded.")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Toggles role and removes reaction if existing reaction role"""
        if payload.user_id == self.bot.user.id: return
        # Get role from reaction (if exists)
        role, user = self.parse_reaction_payload(payload)

        if role is not None and user is not None:
            # Toggle role
            if role not in user.roles: await user.add_roles(role, reason="ReactionRole")
            else: await user.remove_roles(role, reason="ReactionRole")

            # Remove reaction
            channel = self.bot.get_channel(payload.channel_id)
            message = channel.get_partial_message(payload.message_id)
            await message.remove_reaction(payload.emoji, user)

    def parse_reaction_payload(self, payload: discord.RawReactionActionEvent):
        """Looks up the the corresponding role from the RR data"""
        guild_id = payload.guild_id
        ref, msg_data = self.get_msg_from_ids(payload.guild_id, payload.channel_id, payload.message_id)
        if ref is not None and msg_data is not None:
            guild: discord.Guild = self.bot.get_guild(guild_id)
            role = guild.get_role(msg_data["roles"].get(str(payload.emoji)))
            user = guild.get_member(payload.user_id)

            return role, user
        return None, None


    @commands.command(aliases=["rcreate"])
    async def reaction(self, ctx, channel: discord.TextChannel, reference, title, *, message=""):
        """
        Creates a base message to add reactions to.

        **Example:**
        ```WMCS!reaction #get-roles pronouns "Get your Pronouns!" Get your pronouns here!```
        """
        embed = discord.Embed(title=title, description=message)
        embed.add_field(name="Roles", value="_ _", inline=False)
        msg = await channel.send(embed=embed)

        if not self.add_message(ctx.guild.id, msg, reference):
            # If RR of same name already exists
            await msg.delete()
            raise ReferenceAlreadyExists(f"A reaction message with reference `{reference}` already exists.")


    @commands.command(aliases=["radd"])
    async def reaction_add(self, ctx, msg_reference, emote, role: discord.Role, *, description=None):
        """
        Adds a reaction role to a message.

        **Example:**
        ```
        WMCS!reaction_add 🧙‍♂️ @he/him **He/Him Pronouns**
        WMCS!reaction_add 🧙‍♂️ @she/her
        ```
        """

        # Fetch data
        guild: discord.Guild = ctx.guild
        msg_data = self.get_msg_from_ref(guild.id, msg_reference)
        if not msg_data: raise NoMessageExists(f"No message exists with reference `{msg_reference}`.")
        channel = guild.get_channel(msg_data["channelID"])
        message: discord.Message = await channel.fetch_message(msg_data["messageID"])

        emote = self.get_emoji(ctx, emote)

        # Edit embed to include new option
        embed: discord.Embed = message.embeds[0]
        field = embed.fields[0]
        embed.remove_field(0)

        if field.value == "_ _": field.value = ""
        new_val = field.value + f"\n{emote} {description if description is not None else role.name}"
        embed.add_field(name=field.name, value=new_val)
        await message.edit(embed=embed)

        # Add reaction to list
        self.add_reaction(ctx.guild.id, msg_reference, emote, role.id)

        # Add reaction to message
        await message.add_reaction(emote)


    def get_emoji(self, ctx, emote):
        """Gets emoji by name if name provided - checks external emojis as well"""
        if isinstance(emote, discord.Emoji): return emote
        if isinstance(emote, str):
            # Remove :'s
            if emote[0] == ":" and emote[-1] == ":":
                emote = emote[1:-1]
            # Check server emojis first
            result = discord.utils.get(ctx.guild.emojis, name=emote)
            if result is not None: return result
            # If no match, check other servers
            else: return discord.utils.get(self.bot.emojis, name=emote)
        return None


    @commands.command(aliases=["rlist"])
    async def reactions(self, ctx):
        """List all reaction messages on this server."""
        guild_id = ctx.guild.id
        data = self.data.get(str(guild_id), None)
        embed = discord.Embed(title="Reaction Roles")
        if data is None:
            # Blank msg
            embed.description = "There are no reaction roles set up right now."
        else:
            # Lists all RRs
            for reference, msg_data in data.items():
                embed.add_field(**self.msg_field(ctx, reference, msg_data))
        await ctx.send(embed=embed)


    @commands.command(aliases=["rrem", "rdel"])
    async def reaction_remove(self, ctx, reference: str):
        """
        Remove a reaction message.

        Unfortunately, no way is currently provided to remove a single role.

        **Example:**
        ```
        WMCS!reaction_remove pronouns
        ```
        """
        # Fetch data
        guild: discord.Guild = ctx.guild
        guild_id = ctx.guild.id
        data = self.data.get(str(guild_id), None)
        if data is None or data.get(reference) is None:
            raise NoMessageExists(f"No message exists with reference `{reference}`.")

        # Confirm removal message
        embed = discord.Embed(title=f"Remove Reaction Role {reference}")
        embed.description = "React with 🗑️ to confirm removal of message " + reference
        msg_data = data[reference]
        embed.add_field(**self.msg_field(ctx, reference, msg_data))
        msg = await ctx.send(embed=embed)

        if msg_data is not None:
            await msg.add_reaction("🗑️")

            # Wait for reaction
            await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and u == ctx.message.author and str(r.emoji) == "🗑️", timeout=60)
            channel: discord.TextChannel = guild.get_channel(msg_data["channelID"])
            # Delete original message, from both channel and data
            orig_message: discord.PartialMessage = channel.get_partial_message(msg_data["messageID"])
            await orig_message.delete()
            del data[reference]
            self.save_json()


    @staticmethod
    def msg_field(ctx, reference, msg_data):
        """Creates field to represent a RR in self.reactions()"""
        channel_id = msg_data.get("channelID")
        message_id = msg_data.get("messageID")
        field_title = str(reference)
        field_value = f"[message](https://www.discordapp.com/channels/{ctx.guild.id}/{channel_id}/{message_id})"
        for emote, role_id in msg_data["roles"].items():
            field_value += f"\n{emote} {ctx.guild.get_role(role_id)}"
        return {"name": field_title, "value": field_value, "inline": False}



    def add_message(self, guild_id, message: discord.Message, reference):
        """Adds RR record for message"""
        # Initialize guild entry if not existent already
        if not str(guild_id) in self.data:
            self.data[str(guild_id)] = {}

        # If reference already exists
        if self.data[str(guild_id)].get(reference): return False
        # Add data
        self.data[str(guild_id)][reference] = {
            "channelID": message.channel.id,
            "messageID": message.id,
            "roles": {}
        }
        # Save to file
        self.save_json()
        return True


    def add_reaction(self, guild_id, reference, emote, role_id):
        """Adds reaction record to RR reference"""
        self.data[str(guild_id)][reference]["roles"][str(emote)] = role_id
        self.save_json()


    def get_msg_from_ids(self, guild_id, channel_id, message_id):
        """Finds reference and message data for RR from IDs"""
        data = self.data.get(str(guild_id), None)
        if data is not None:
            for ref, msg in data.items():
                if channel_id == msg.get("channelID") and message_id == msg.get("messageID"):
                    return ref, msg
        return None, None


    def get_msg_from_ref(self, guild_id, reference):
        """Finds message data for RR from ref"""
        data = self.data.get(str(guild_id), None)
        if data is not None:
            msg_data = data.get(reference)
            return msg_data


class ReferenceAlreadyExists(Exception):
    def __init__(self, str):
        super().__init__(str)


class NoMessageExists(Exception):
    def __init__(self, str):
        super().__init__(str)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
