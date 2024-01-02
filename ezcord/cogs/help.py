from __future__ import annotations

import inspect
import random
from copy import deepcopy

from .. import emb
from ..bot import Bot, Cog
from ..components import View
from ..enums import HelpStyle
from ..internal import replace_embed_values, t
from ..internal.dc import PYCORD, discord, slash_command
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
        if not value:
            continue
        s = s.replace(f"{{{key}}}", value)
    return s


def get_perm_parent(cmd: discord.SlashCommand) -> discord.SlashCommandGroup | None:
    """Iterates through parent groups until it finds a group with default_member_permissions set."""
    if PYCORD:
        while cmd.default_member_permissions is None:
            cmd = cmd.parent
            if cmd is None:
                return None

        return cmd.default_member_permissions

    else:
        while cmd.default_permissions is None:
            cmd = cmd.parent
            if cmd is None:
                return None

        return cmd.default_permissions


async def pass_checks(command: discord.SlashCommand, ctx) -> bool:
    """Returns True if the current user passes all checks (Pycord only)."""
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

    @slash_command(name=t("cmd_name"), description=t("cmd_description"))
    async def help(self, ctx):
        embed = self.bot.help.embed
        if embed is None:
            embed = discord.Embed(
                title=t("embed_title", i=ctx.interaction), color=discord.Color.blue()
            )
        else:
            interaction = ctx.interaction if PYCORD else ctx
            embed = replace_embed_values(embed, interaction)

        options = []
        commands: dict[str, dict] = {}
        for name, cog in self.bot.cogs.items():
            if hasattr(cog, "hidden") and cog.hidden:
                continue

            group = get_group(cog)
            name = group if group else name
            name = name.title()

            if len(name) == 0:
                log.warning(
                    "A cog has a name with length 0. "
                    "This cog will not be displayed in the help command."
                )
                continue

            if len(name) > 100:
                name = name[:90] + "..."

            if name not in commands:
                commands[name] = {}
            if "cmds" not in commands[name]:
                commands[name]["cmds"] = []

            if len(cog.get_commands()) == 0 and PYCORD:
                continue

            emoji = get_emoji(cog)
            commands[name]["emoji"] = emoji

            desc = cog.description
            if not cog.description:
                desc = t("default_description", name, i=ctx)
                if not desc:
                    log.warning(
                        f"The default description for cog '{name}' is invalid. "
                        f"This can be changed in the language file."
                    )

            commands[name]["description"] = desc

            field_name = replace_placeholders(self.bot.help.title, name=name, emoji=emoji)
            desc = replace_placeholders(
                self.bot.help.description, description=desc, name=name, emoji=emoji
            )

            if PYCORD:
                cog_cmds = [
                    cmd
                    for cmd in cog.walk_commands()
                    if type(cmd)
                    not in [discord.MessageCommand, discord.UserCommand, discord.SlashCommandGroup]
                ]
            else:
                cog_cmds = cog.walk_app_commands()

            for command in cog_cmds:
                if PYCORD:
                    default_perms = command.default_member_permissions
                    guild_ids = command.guild_ids
                else:
                    default_perms = command.default_permissions
                    guild_ids = command._guild_ids

                if self.bot.help.permission_check:
                    if PYCORD and not await pass_checks(command, ctx):
                        continue

                    if default_perms and not command.parent:
                        if not default_perms.is_subset(ctx.user.guild_permissions):
                            continue

                    parent_perms = get_perm_parent(command)
                    if parent_perms and not parent_perms.is_subset(ctx.user.guild_permissions):
                        continue

                if ctx.guild and guild_ids and ctx.guild.id not in guild_ids:
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
            return await ctx.response.send_message(t("no_commands", i=ctx), ephemeral=True)
        if len(options) > 25 or len(embed.fields) > 25:
            log.error(
                f"Help command category limit reached. Only 25 out of {len(options)} are shown."
            )
            options = options[:25]
            embed.fields = embed.fields[:25]

        sorted_options = sorted(options, key=lambda x: [char for char in x.label if char.isalpha()])
        embed.fields = sorted(embed.fields, key=lambda x: x.name.lower())
        view = CategoryView(sorted_options, self.bot, ctx.user, commands, ctx)
        for button in self.bot.help.buttons:
            view.add_item(deepcopy(button))
        await ctx.response.send_message(view=view, embed=embed, ephemeral=self.bot.help.ephemeral)


class CategorySelect(discord.ui.Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        bot: Bot,
        member: discord.Member | discord.User,
        commands: dict[str, dict],
        interaction,
    ):
        super().__init__(
            min_values=1, max_values=1, placeholder=t("placeholder", i=interaction), options=options
        )
        self.bot = bot
        self.member = member
        self.commands = commands

    def get_mention(self, cmd) -> str:
        """This is only needed for Discord.py."""
        if self.bot.all_dpy_commands:
            for c in self.bot.all_dpy_commands:
                if c.name == cmd.name:
                    cmd = c
                    break

        try:
            return cmd.mention
        except AttributeError:
            return f"**/{cmd.name}**"

    async def callback(self, interaction: discord.Interaction):
        if self.bot.help.author_only and interaction.user != self.member:
            return await emb.error(interaction, t("wrong_user", i=interaction))

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
                    name=f"**{self.get_mention(command)}**",
                    value=f"`{command.description}`",
                    inline=False,
                )

        elif style == HelpStyle.codeblocks or style == HelpStyle.codeblocks_inline:
            for command in commands:
                embed.add_field(
                    name=f"**{self.get_mention(command)}**",
                    value=f"```{command.description}```",
                    inline=style == HelpStyle.codeblocks_inline,
                )

        elif style == HelpStyle.embed_description:
            embed.description = desc + "\n"
            for command in commands:
                if len(embed.description) <= 3500:
                    embed.description += (
                        f"**{self.get_mention(command)}**\n{command.description}\n\n"
                    )
                else:
                    log.error("Help embed length limit reached. Some commands are not shown.")
                    break

        elif style == HelpStyle.markdown:
            embed.description = desc
            for command in commands:
                if len(embed.description) <= 3500:
                    embed.description += f"### {self.get_mention(command)}\n{command.description}\n"
                else:
                    log.error("Help embed length limit reached. Some commands are not shown.")
                    break

        if len(commands) == 0:
            embed.description = t("no_commands", i=interaction)

        view = CategoryView(self.options, self.bot, self.member, self.commands, interaction)
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
        interaction: discord.Interaction,
    ):
        if PYCORD:
            super().__init__(timeout=bot.help.timeout, disable_on_timeout=True)
        else:
            super().__init__(timeout=None)

        self.add_item(CategorySelect(options, bot, member, commands, interaction))
