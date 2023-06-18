from __future__ import annotations

import random

import discord
from discord.commands import slash_command

from ..bot import Bot, Cog
from ..components import EzView
from ..internal import t


def get_emoji(cog: Cog) -> str:
    if hasattr(cog, "emoji") and cog.emoji:
        emoji = cog.emoji
    else:
        emoji = random.choice(["🔰", "👻", "📝", "👥", "🦕", "🐧"])

    return emoji


def get_group(cog: Cog) -> str | None:
    if hasattr(cog, "group") and cog.group:
        return cog.group
    return None


class Help(Cog, command_attrs=dict(hidden=True)):
    @slash_command(name="help", description=t("cmd_description"), hidden=True)
    async def help(self, ctx):
        embed = self.bot.help["embed"]
        if embed is None:
            embed = discord.Embed(title=t("embed_title"), color=discord.Color.blue())

        options = []
        commands = {}
        for name, cog in self.bot.cogs.items():
            group = get_group(cog)
            name = group if group else name
            name = name.title()
            if name not in commands:
                commands[name] = {}
            if "cmds" not in commands[name]:
                commands[name]["cmds"] = []

            if len(cog.get_commands()) == 0 or cog == self:
                continue

            emoji = get_emoji(cog)
            emoji_str = f"`{emoji}` ・ "
            commands[name]["emoji"] = emoji

            desc = cog.description
            if not cog.description:
                desc = t("default_description", name)

            for command in cog.walk_commands():
                if type(command) in [
                    discord.MessageCommand,
                    discord.UserCommand,
                    discord.SlashCommandGroup,
                ]:
                    continue

                commands[name]["cmds"].append(command)

            if not group:
                embed.add_field(name=f"{emoji_str or ''}{name}", value=desc, inline=False)
                option = discord.SelectOption(label=name, emoji=emoji)
                options.append(option)

        view = CategoryView(options, self.bot, ctx.user, commands)
        await ctx.respond(view=view, embed=embed, ephemeral=self.bot.help["ephemeral"])


def setup(bot: Bot):
    bot.add_cog(Help(bot))


class CategorySelect(discord.ui.Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        bot: Bot,
        member: discord.Member | discord.User,
        commands: dict[str, dict],
    ):
        super().__init__(min_values=1, max_values=1, placeholder=t("placeholder"), options=options)
        self.bot = bot
        self.member = member
        self.commands = commands

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.member:
            return await interaction.response.send_message(t("wrong_user"), ephemeral=True)

        cmds = self.commands[self.values[0]]
        title = self.values[0].title()
        emoji = cmds["emoji"]

        embed = self.bot.help["embed"]
        if embed is None:
            embed = discord.Embed(
                title=f"`{emoji}` - {title}",
                color=discord.Color.blue(),
            )
        for command in cmds["cmds"]:
            embed.add_field(
                name=f"{command.mention}",
                value=f"`{command.description}`",
                inline=False,
            )

        await interaction.response.edit_message(
            embed=embed, view=CategoryView(self.options, self.bot, self.member, self.commands)
        )


class CategoryView(EzView):
    def __init__(
        self,
        options: list[discord.SelectOption],
        bot: Bot,
        member: discord.Member | discord.User,
        commands: dict[str, dict],
    ):
        super().__init__(timeout=500, disable_on_timeout=True)
        self.add_item(CategorySelect(options, bot, member, commands))
