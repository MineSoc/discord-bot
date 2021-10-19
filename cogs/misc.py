import io
import re

import discord

from discord.ext.commands import Cog, command
from PIL import Image, ImageFont, ImageDraw

import utils.utils
from cogs.msg_edit import MsgEdit

class Misc(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.font: ImageFont.ImageFont = ImageFont.truetype("resources/MinecraftTen.ttf", 90)
        self.subfont: ImageFont.ImageFont = ImageFont.truetype("resources/Minecraft.otf", 45)
        self.main_colour = (255, 255, 255)
        self.outline_colour = (0, 0, 0)

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

    # TODO Welcome message + assign ping party
    # @Cog.listener
    # async def on_member_join(self, member):
    #     await member.send("hello")

    @command()
    async def title(self, ctx, *, title: str):
        """
        Generates a title image, in a Minecraft style font. Use [A] to produce the creeper face version.

        **Example:**
        ```WMCS!title Survival Tuesdays```
        """
        await ctx.send(file=self.create_title(title))


    def create_title(self, title):
        title = title.replace("[A]", "ƒ")
        w, h = self.font.getsize(title)
        outline = 5
        img: Image.Image = Image.new('RGBA', (w + outline + 6, h + outline + 10))
        d = ImageDraw.Draw(img)

        d.text((outline / 2 + 3, outline - 3), title, font=self.font, fill=self.main_colour, stroke_width=outline, stroke_fill=self.outline_colour)

        return self.to_file(img)

    def create_subtitle(self, title):
        w, h = self.subfont.getsize(title)
        outline = 5
        img: Image.Image = Image.new('RGBA', (w*2 + outline + 6, h + outline + 10))
        d = ImageDraw.Draw(img)

        d.text((img.width/2 - w/2, outline - 3), title, font=self.subfont, fill=self.main_colour, stroke_width=outline, stroke_fill=self.outline_colour)

        return self.to_file(img)


    @staticmethod
    def to_file(img):
        with io.BytesIO() as img_bin:
            img.save(img_bin, 'PNG')
            img_bin.seek(0)
            return discord.File(fp=img_bin, filename='title.png')


def setup(bot):
    bot.add_cog(Misc(bot))