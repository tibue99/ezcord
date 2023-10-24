from __future__ import annotations

import inspect
import random
from copy import deepcopy

from .. import emb
from ..bot import Bot, Cog
from ..components import View
from ..enums import HelpStyle
from ..internal import replace_embed_values, t
from ..internal.dc import discord
from ..logs import log


def get_emoji(cog: Cog) -> str:
    if hasattr(cog, "emoji") and cog.emoji:
        emoji = cog.emoji
    else:
        emoji = random.choice(["🔰", "👻", "🍪", "👥", "🦕", "🐧", "✨", "😩", "🍔"])

    return emoji


def get_group(cog: Cog) -> str | None:
    if hasattr(cog, "group") and cog.group:
        return cog.group
    return None


def replace_placeholders(s: str, **kwargs: str):
    for key, value in kwargs.items():
        s = s.replace(f"{{{key}}}", value)
    return s


def get_perm_parent(cmd: discord.SlashCommand) -> discord.SlashCommandGroup | None:
    """Iterates through parent groups until it finds a group with default_member_permissions set."""
    while cmd.default_member_permissions is None:
        cmd = cmd.parent
        if cmd is None:
            return None

    return cmd


async def pass_checks(command: discord.SlashCommand, ctx: discord.ApplicationContext) -> bool:
    """Returns True if the current user passes all checks."""
    passed = True
    for check in deepcopy(command.checks):
        try:
            if inspect.iscoroutinefunction(check):
                await check(ctx)
            else:
                if not check(ctx):
                    passed = False
                    break
        except Exception:
            passed = False
            break

    return passed


class Help(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.help.guild_only = bot.help.guild_only

    @discord.slash_command(name=t("cmd_name"), description=t("cmd_description"))
    async def help(self, ctx: discord.ApplicationContext):
        embed = self.bot.help.embed
        if embed is None:
            embed = discord.Embed(title=t("embed_title"), color=discord.Color.blue())
        else:
            embed = replace_embed_values(embed, ctx.interaction)

        options = []
        commands: dict[str, dict] = {}
        for name, cog in self.bot.cogs.items():
            if hasattr(cog, "hidden") and cog.hidden:
                continue

            group = get_group(cog)
            name = group if group else name
            name = name.title()
            if name not in commands:
                commands[name] = {}
            if "cmds" not in commands[name]:
                commands[name]["cmds"] = []

            if len(cog.get_commands()) == 0:
                continue

            emoji = get_emoji(cog)
            commands[name]["emoji"] = emoji

            desc = cog.description
            if not cog.description:
                desc = t("default_description", name)

            commands[name]["description"] = desc

            field_name = replace_placeholders(self.bot.help.title, name=name, emoji=emoji)
            desc = replace_placeholders(
                self.bot.help.description, description=desc, name=name, emoji=emoji
            )

            for command in cog.walk_commands():
                if type(command) in [
                    discord.MessageCommand,
                    discord.UserCommand,
                    discord.SlashCommandGroup,
                ]:
                    continue

                if self.bot.help.permission_check:
                    if not await pass_checks(command, ctx):
                        continue

                    if command.default_member_permissions and not command.parent:
                        if not command.default_member_permissions.is_subset(
                            ctx.author.guild_permissions
                        ):
                            continue

                    parent = get_perm_parent(command)
                    if parent and not parent.default_member_permissions.is_subset(
                        ctx.author.guild_permissions
                    ):
                        continue

                if ctx.guild and command.guild_ids and ctx.guild.id not in command.guild_ids:
                    continue

                commands[name]["cmds"].append(command)

            cmd_count = len(commands[name]["cmds"])

            if cmd_count == 0:
                continue
            if not group:
                if self.bot.help.show_cmd_count:
                    label = f"{name} ({cmd_count})"
                else:
                    label = name
                option = discord.SelectOption(label=label, emoji=emoji, value=name)
                options.append(option)
                if self.bot.help.show_categories:
                    embed.add_field(name=field_name, value=desc, inline=False)

        if len(options) == 0:
            return await ctx.respond(t("no_commands"), ephemeral=True)
        if len(options) > 25 or len(embed.fields) > 25:
            log.error(
                f"Help command category limit reached. Only 25 out of {len(options)} are shown."
            )
            options = options[:25]
            embed.fields = embed.fields[:25]
        view = CategoryView(options, self.bot, ctx.user, commands)
        for button in self.bot.help.buttons:
            view.add_item(deepcopy(button))
        await ctx.respond(view=view, embed=embed, ephemeral=self.bot.help.ephemeral)


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
        if self.bot.help.author_only and interaction.user != self.member:
            return await emb.error(interaction, t("wrong_user"))

        cmds = self.commands[self.values[0]]
        title = self.values[0].title()
        emoji = cmds["emoji"]

        embed = self.bot.help.embed
        if embed is None:
            embed = discord.Embed(
                color=discord.Color.blue(),
            )
        else:
            embed = replace_embed_values(embed, interaction)
        embed.title = replace_placeholders(self.bot.help.title, name=title, emoji=emoji)
        embed.clear_fields()

        if self.bot.help.show_description:
            embed.description = desc = cmds["description"] + "\n"
        else:
            desc = ""

        commands = cmds["cmds"]
        embed_field_styles = [
            HelpStyle.embed_fields,
            HelpStyle.codeblocks_inline,
            HelpStyle.codeblocks,
        ]
        style = self.bot.help.style
        if len(commands) > 25 and style in embed_field_styles:
            style = HelpStyle.embed_description

        if style == HelpStyle.embed_fields:
            for command in commands:
                embed.add_field(
                    name=f"**{command.mention}**",
                    value=f"`{command.description}`",
                    inline=False,
                )

        elif style == HelpStyle.codeblocks or style == HelpStyle.codeblocks_inline:
            for command in commands:
                embed.add_field(
                    name=f"**{command.mention}**",
                    value=f"```{command.description}```",
                    inline=style == HelpStyle.codeblocks_inline,
                )

        elif style == HelpStyle.embed_description:
            embed.description = desc
            for command in commands:
                if len(embed.description) <= 3500:
                    embed.description += f"**{command.mention}**\n{command.description}\n\n"
                else:
                    log.error("Help embed length limit reached. Some commands are not shown.")
                    break

        elif style == HelpStyle.markdown:
            embed.description = desc
            for command in commands:
                if len(embed.description) <= 3500:
                    embed.description += f"### {command.mention}\n{command.description}\n"
                else:
                    log.error("Help embed length limit reached. Some commands are not shown.")
                    break

        if len(commands) == 0:
            embed.description = t("no_commands")

        view = CategoryView(self.options, self.bot, self.member, self.commands)
        for button in self.bot.help.buttons:
            view.add_item(deepcopy(button))
        await interaction.response.edit_message(embed=embed, view=view)


class CategoryView(View):
    def __init__(
        self,
        options: list[discord.SelectOption],
        bot: Bot,
        member: discord.Member | discord.User,
        commands: dict[str, dict],
    ):
        super().__init__(timeout=bot.help.timeout, disable_on_timeout=True)
        self.add_item(CategorySelect(options, bot, member, commands))
