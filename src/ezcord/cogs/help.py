from __future__ import annotations

import random

import discord
from discord.commands import slash_command

from ..bot import Bot, Cog
from ..components import EzView
from ..internal import t


def get_emoji(cog):
    if hasattr(cog, "emoji") and cog.emoji:
        emoji = cog.emoji
    else:
        emoji = random.choice(["🔰", "👻", "📝", "👥", "🦕", "🐧"])

    return emoji


class Help(Cog, command_attrs=dict(hidden=True)):
    @slash_command(name="help", description=t("cmd_description"), hidden=True)
    async def help(self, ctx):
        embed = self.bot.help["embed"]
        if embed is None:
            embed = discord.Embed(title=t("embed_title"), color=discord.Color.blue())

        options = []

        for name, cog in zip(self.bot.cogs.keys(), self.bot.cogs.values()):
            name = name.title()

            if len(cog.get_commands()) == 0 or cog == self:
                continue

            emoji = get_emoji(cog)
            emoji_str = f"`{emoji}` ・ "

            desc = cog.description
            if not cog.description:
                desc = t("default_description", name)

            embed.add_field(name=f"{emoji_str or ''}{name}", value=desc, inline=False)

            option = discord.SelectOption(label=name, value=name, emoji=emoji)
            options.append(option)

        view = View(options, self.bot, ctx.user)
        await ctx.respond(view=view, embed=embed, ephemeral=self.bot.help["ephemeral"])


def setup(bot: Bot):
    bot.add_cog(Help(bot))


class Select(discord.ui.Select):
    def __init__(
        self, options: list[discord.SelectOption], bot: Bot, member: discord.Member | discord.User
    ):
        super().__init__(min_values=1, max_values=1, placeholder=t("placeholder"), options=options)
        self.bot = bot
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.member:
            return await interaction.response.send_message(t("wrong_user"), ephemeral=True)

        embed = None
        for name, cog in zip(self.bot.cogs.keys(), self.bot.cogs.values()):
            if self.values[0] != name:
                continue

            title = name.title()
            emoji = get_emoji(cog)

            embed = self.bot.help["embed"]
            if embed is None:
                embed = discord.Embed(
                    title=f"`{emoji}` - {title}",
                    color=discord.Color.blue(),
                )
            for command in cog.walk_commands():
                if type(command) in [
                    discord.MessageCommand,
                    discord.UserCommand,
                    discord.SlashCommandGroup,
                ]:
                    continue

                embed.add_field(
                    name=f"{command.mention}",
                    value=f"`{command.description}`",
                    inline=False,
                )

                if embed.fields > 25:
                    print("Too many fields") # Could be replaced by the logger
                    break


        await interaction.response.edit_message(
            embed=embed, view=View(self.options, self.bot, self.member)
        )


class View(EzView):
    def __init__(
        self, options: list[discord.SelectOption], bot: Bot, member: discord.Member | discord.User
    ):
        super().__init__(timeout=500, disable_on_timeout=True)
        self.add_item(Select(options, bot, member))

