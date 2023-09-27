import io
import os
import re
from typing import Optional, Union

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

import utils
from cogs.msg_edit import MsgEdit

PING_ROLE = os.getenv("WMCS_PING_ROLE")
if not PING_ROLE:
    PING_ROLE = "ping party"


class Announcements(utils.ExecCog):
    """Prepares announcements and titles - @Exec only"""

    bot: commands.Bot

    def __init__(self, bot):
        # super(Announcements, self).__init__("announcements.json")
        self.bot = bot
        self.font: ImageFont.ImageFont = ImageFont.truetype(
            "resources/MinecraftTen.ttf", 90
        )
        self.subfont: ImageFont.ImageFont = ImageFont.truetype(
            "resources/Minecraft.otf", 45
        )
        self.main_colour = (255, 255, 255)
        self.outline_colour = (0, 0, 0)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def title(self, ctx, *, title: str):
        """
        Generates a title image, in a Minecraft style font. Use [A] to produce the creeper face version.

        **Example:**
        ```WMCS!title Survival Tuesdays```
        """
        await ctx.send(file=self.create_title(title))

    # async def get_callout(self, ctx: commands.Context, name):
    #     data = self.guild_data(ctx.guild.id)
    #     if callouts := data.get("callouts", None):
    #         return callouts.get(name, None)
    #     return None

    # @command()
    # async def add_callout(self, ctx: commands.Context, name: str, emoji: discord.Emoji, *, text: str):
    #     data = self.guild_data(ctx.guild.id)
    #     data

    # noinspection PyTypeHints
    @commands.command(usage="WMCS!announce <channel> <announcement | source msg link>")
    @commands.bot_has_permissions(
        send_messages=True, add_reactions=True, embed_links=True, attach_files=True
    )
    async def announce(
        self,
        ctx: commands.Context,
        channel: utils.BotHasPermsInChannel(send_messages=True, attach_files=True),
        *,
        announcement: Union[discord.Message, str],
    ):
        """
        Posts an announcement. Generates headings as images.
        `# <Title>` creates a title - use [A] for creeper face A.
        `## <Subtitle>` creates a subtitle
        `IMG <link>` will insert an image
        A line reading `BREAK` will break the message at that point.
        All usual discord formatting works, including external emojis (if bot is in that server).
        For embeds/buttons, use `WMCS!setembed`/`WMCS!setbuttons`

        Once posted, you may edit the announcement with WMCS!setmsg <url> <content>

        ✏️ Edit will update the announcement to match any *edits to the original command message.*
        **Example**
        ```
        WMCS!announce #events
        # Announcement
        This is a **demo announcement**
        Awkwardly showcasing features
        ## Emoji Example
        External emoji: :wool_orange:
        BREAK
        new message
        IMG https://picsum.photos/seed/a/400/200
        ```
        """

        # If message is provided,
        if isinstance(announcement, discord.Message):
            an_msg = announcement
            announcement: str = announcement.content

            # Remove WMCS!announce #<channel> from start of announcement
            prefixes = await ctx.bot.get_prefix(an_msg)

            def check_pref():
                for pref in prefixes:
                    cmd = pref + "announce "
                    if announcement.startswith(cmd):
                        return pref, announcement[len(cmd) :]

            if p := check_pref():
                pref, cmd = p
                # Remove channel and following whitespace
                search = re.search(
                    "^((<#[0-9]{15,20}>)|(#?\\S+))(\s|\\n)* (.+)$", cmd, re.DOTALL
                )
                if search:
                    announcement = search.group(5)

        lines = announcement.split("\n")
        accumulated_lines = []
        messages = []

        # Wrappers for adding message to messages after sending
        async def send(**kwargs):
            messages.append(await ctx.send(**kwargs))

        async def send_lines():
            concat = "\n".join(accumulated_lines)
            try:
                await send(content=MsgEdit.remove_placeholders(ctx, concat))
            except discord.HTTPException:
                pass
            accumulated_lines.clear()

        # Send each line
        for line in lines:
            # Find each type
            sub_group = re.search(r"^## ?(.+)$", line)
            title_group = re.search(r"^# ?(.+)$", line)
            img_group = re.search(r"^IMG (.+)$", line)
            break_group = re.search(r"^BREAK$", line)
            # Empty out any lines
            if sub_group or title_group or img_group or break_group:
                if accumulated_lines:
                    await send_lines()

                if sub_group:  # Subtitle
                    await send(file=self.create_subtitle(sub_group.group(1)))
                elif title_group:  # Title
                    await send(file=self.create_title(title_group.group(1)))
                elif img_group:  # Image
                    await send(content=img_group.group(1))
                elif break_group:
                    pass

            else:  # Is just text
                if (len(accumulated_lines) + len(line)) > 1900:
                    await send_lines()
                accumulated_lines.append(line)

        # Post remaining message
        if accumulated_lines:
            await send_lines()

        # Function for reaction to confirm message
        async def confirm(msg, reaction):
            # If edit or delete, remove old messages
            if str(reaction) in {"❌", "✏️"}:
                await self.remove_msgs(*messages, msg)

                if str(reaction) == "✏️":
                    edit_msg: discord.Message = await ctx.fetch_message(ctx.message.id)
                    await ctx.bot.process_commands(edit_msg)
                return

            # Copy all messages
            for ann_msg in messages:
                if ann_msg.attachments:
                    await channel.send(ann_msg.attachments[0].url)
                elif ann_msg.content:
                    await channel.send(content=ann_msg.content)

            # If pinging, find ping party role
            role = discord.utils.get(ctx.guild.roles, name=PING_ROLE)
            if str(reaction) == "🏓" and role:
                await channel.send(role.mention)

            await msg.clear_reactions()
            await ctx.message.add_reaction("👍")
            # Once posted, remove old messages
            # await self.remove_msgs(*messages, msg)
            await self.remove_msgs(msg)

        async def timeout(msg):
            await ctx.send(
                f"**Timeout.** Restart posting with: `WMCS!announce #{channel.name} {ctx.message.jump_url}`"
            )
            await self.remove_msgs(*messages, msg)

        await utils.utils.confirmation(
            ctx,
            f"Confirm posting to #{channel.name}",
            f"🏓 will post and ping @{PING_ROLE}\n  ✅ will just post\n  ✏️ to edit (change original first)\n  ❌ to cancel",
            ["🏓", "✅", "✏️", "❌"],
            confirm,
            timeout,
            300,
        )

    @staticmethod
    async def remove_msgs(*messages):
        for ann_msg in messages:
            await ann_msg.delete()

    def create_title(self, title):
        title = title.replace("[A]", "ƒ")
        _, _, w, h = self.font.getbbox(title)
        outline = 5
        img: Image.Image = Image.new("RGBA", (w + outline + 6, h + outline + 10))
        d = ImageDraw.Draw(img)

        d.text(
            (outline / 2 + 3, outline - 3),
            title,
            font=self.font,
            fill=self.main_colour,
            stroke_width=outline,
            stroke_fill=self.outline_colour,
        )

        return self.to_file(img)

    def create_subtitle(self, title):
        _, _, w, h = self.subfont.getbbox(title)
        outline = 5
        img: Image.Image = Image.new("RGBA", (w * 2 + outline + 6, h + outline + 10))
        d = ImageDraw.Draw(img)

        d.text(
            (img.width / 2 - w / 2, outline - 3),
            title,
            font=self.subfont,
            fill=self.main_colour,
            stroke_width=outline,
            stroke_fill=self.outline_colour,
        )

        return self.to_file(img)

    @staticmethod
    def to_file(img):
        with io.BytesIO() as img_bin:
            img.save(img_bin, "PNG")
            img_bin.seek(0)
            return discord.File(fp=img_bin, filename="title.png")


def setup(bot):
    bot.add_cog(Announcements(bot))
