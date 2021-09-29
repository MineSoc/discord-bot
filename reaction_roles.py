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
    async def reaction(self, ctx, channel: discord.TextChannel, title, message):
        embed = discord.Embed(title=title, description=message)
        embed.add_field(name="Roles", value="_ _", inline=False)
        await channel.send(embed=embed)

    @commands.has_permissions(manage_channels=True)
    @commands.command(help="Add reaction to reaction message")
    async def reaction_add(self, ctx, channel: discord.TextChannel, message_id, emote, role: discord.Role, description=None):
        print(f"Adding role {role.name} for emoji {emote}")
        message: discord.Message = await channel.fetch_message(message_id)
        if message.author == self.bot.user:
            embed: discord.Embed = message.embeds[0]
            field: EmbedProxy = embed.fields[0]
            embed.remove_field(0)

            if field.value == "_ _": field.value = ""
            new_val = field.value + f"\n{emote} {description if description is not None else role.name}"
            embed.add_field(name=field.name, value=new_val)
            await message.edit(embed=embed)

        await message.add_reaction(emote)
        self.add_reaction(ctx.guild.id, emote, role.id, channel.id, message_id)



    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def reactions(self, ctx):
        guild_id = ctx.guild.id
        data = reaction_roles_data.get(str(guild_id), None)
        embed = discord.Embed(title="Reaction Roles")
        if data is None:
            embed.description = "There are no reaction roles set up right now."
        else:
            for index, rr in enumerate(data):
                emote = rr.get("emote")
                role_id = rr.get("roleID")
                role = ctx.guild.get_role(role_id)
                channel_id = rr.get("channelID")
                message_id = rr.get("messageID")
                embed.add_field(
                    name=str(index),
                    value=f"{emote} - @{role} - [message](https://www.discordapp.com/channels/{guild_id}/{channel_id}/{message_id})",
                    inline=False,
                )
        await ctx.send(embed=embed)


    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def reaction_remove(self, ctx, index: int):
        guild_id = ctx.guild.id
        data = reaction_roles_data.get(str(guild_id), None)
        embed = discord.Embed(title=f"Remove Reaction Role {index}")
        rr = None
        if data is None:
            embed.description = "Given Reaction Role was not found."
        else:
            embed.description = (
                "Do you wish to remove the reaction role below? Please react with 🗑️."
            )
            rr = data[index]
            emote = rr.get("emote")
            role_id = rr.get("roleID")
            role = ctx.guild.get_role(role_id)
            channel_id = rr.get("channelID")
            message_id = rr.get("messageID")
            _id = rr.get("id")
            embed.set_footer(text=_id)
            embed.add_field(
                name=str(index),
                value=f"{emote} - @{role} - [message](https://www.discordapp.com/channels/{guild_id}/{channel_id}/{message_id})",
                inline=False,
            )
        msg = await ctx.send(embed=embed)
        if rr is not None:
            await msg.add_reaction("🗑️")

            def check(reaction, user):
                return (
                    reaction.message.id == msg.id
                    and user == ctx.message.author
                    and str(reaction.emoji) == "🗑️"
                )

            reaction, user = await self.bot.wait_for("reaction_add", check=check)
            data.remove(rr)
            reaction_roles_data[str(guild_id)] = data
            store_reaction_roles()

    def add_reaction(self, guild_id, emote, role_id, channel_id, message_id):
        if not str(guild_id) in reaction_roles_data:
            reaction_roles_data[str(guild_id)] = []
        reaction_roles_data[str(guild_id)].append(
            {
                "id": str(uuid.uuid4()),
                "emote": emote,
                "roleID": role_id,
                "channelID": channel_id,
                "messageID": int(message_id),
            }
        )
        store_reaction_roles()

    def parse_reaction_payload(self, payload: discord.RawReactionActionEvent):
        guild_id = payload.guild_id
        data = reaction_roles_data.get(str(guild_id), None)
        print(payload)
        print(data)
        if data is not None:
            for rr in data:
                if payload.message_id == rr.get("messageID") and payload.channel_id == rr.get("channelID") and str(payload.emoji) == rr.get("emote"):
                    guild = self.bot.get_guild(guild_id)
                    role = guild.get_role(rr.get("roleID"))
                    user = guild.get_member(payload.user_id)
                    return role, user
        return None, None


def setup(bot):
    bot.add_cog(ReactionRoles(bot))