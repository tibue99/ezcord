from __future__ import annotations

import asyncio
import logging
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import aiohttp
from dotenv import load_dotenv

from .emb import EzContext
from .emb import error as error_emb
from .enums import CogLog, HelpStyle, ReadyEvent
from .errors import ErrorMessageSent
from .i18n import I18N
from .internal import (
    READY_TITLE,
    EzConfig,
    get_error_text,
    localize_cog,
    localize_command,
    print_custom_ready,
    print_ready,
    tr,
)
from .internal.config import Blacklist
from .internal.dc import (
    DPY,
    PYCORD,
    AutoShardedBot,
    CogMeta,
    bridge,
    checks,
    commands,
    discord,
)
from .logs import DEFAULT_LOG, custom_log, set_log
from .sql import DBHandler, PGHandler
from .times import dc_timestamp

if PYCORD:
    _main_bot = discord.Bot
else:
    _main_bot = commands.Bot

if TYPE_CHECKING:
    import discord  # type: ignore
    from discord.ext import commands  # type: ignore

    if hasattr(discord, "Bot"):
        _main_bot = discord.Bot
    else:
        _main_bot = commands.Bot


class Bot(_main_bot):  # type: ignore
    """The EzCord bot class. This is a subclass of :class:`discord.Bot` if you use Pycord.

    .. hint::

        As this class extends from :class:`discord.Bot`, only slash commands are supported.
        If you want to use prefix commands with ``Pycord``, use :class:`PrefixBot` instead.

        If you use ``Discord.py``, you can use this class for both slash and prefix commands.

    Parameters
    ----------
    intents:
        The intents to use for the bot. Defaults to :meth:`discord.Intents.default()`.
    debug:
        Enable log messages. Defaults to ``True``.
    error_handler:
        Enable the error handler. Defaults to ``True``.
    error_webhook_url:
        The webhook URL to send error messages to. Defaults to ``None``.

        .. note::
            You can disable the default error handler, but still provide an error webhook URL.
            This will send an error report to the webhook, but it won't send an error message to the user.
    ignored_errors:
        A list of error types to ignore. Defaults to ``None``.
    full_error_traceback:
        Whether to send the full error traceback. If this is ``False``,
        only the most recent traceback will be sent. Defaults to ``False``.
    language:
        The language to use for user output. If this is set to ``auto``,
        the bot will use the language of the interaction locale whenever possible.
    default_language:
        The default language to use if the interaction locale is not available.
        Defaults to ``"en"``. ``en`` and ``de`` are available by default, but you can add your own
        language as described in :doc:`the language example </examples/languages>`.
    ready_event:
        The style for :meth:`on_ready_event`. Defaults to :attr:`.ReadyEvent.default`.
        If this is ``None``, the event will be disabled.
    **kwargs:
        Additional keyword arguments for :class:`discord.Bot`.
    """

    def __init__(
        self,
        intents: discord.Intents = discord.Intents.default(),
        *,
        debug: bool = True,
        error_handler: bool = True,
        error_webhook_url: str | None = None,
        ignored_errors: list[Any] | None = None,
        full_error_traceback: bool = False,
        language: str = "auto",
        default_language: str = "en",
        ready_event: ReadyEvent | None = ReadyEvent.default,
        **kwargs,
    ):
        if PYCORD:
            super().__init__(intents=intents, **kwargs)
        else:
            prefix = kwargs.pop("command_prefix", None)
            super().__init__(command_prefix=prefix or "!", intents=intents, **kwargs)

        if error_webhook_url:
            os.environ.setdefault("ERROR_WEBHOOK_URL", error_webhook_url)

        if debug:
            self.logger = set_log(DEFAULT_LOG)
        else:
            self.logger = logging.getLogger(DEFAULT_LOG)
            self.logger.addHandler(logging.NullHandler())

        self.error_handler = error_handler
        self.error_webhook_url = error_webhook_url
        self.ignored_errors = ignored_errors or []
        self.full_error_traceback = full_error_traceback

        EzConfig.lang = language
        EzConfig.default_lang = default_language

        self.error_event_added = False
        if error_handler or error_webhook_url:
            self.error_event_added = True
            if DPY:
                self.tree.on_error = self._error_event
            else:
                self.add_listener(self._error_event, "on_application_command_error")

        self.ready_event = ready_event
        if ready_event:
            self.add_listener(self._ready_event, "on_ready")
        self.add_listener(self._check_cog_groups, "on_ready")
        self.add_listener(self._db_setup, "on_connect")

        self.ready_event_adds: dict = {}
        self.ready_event_removes: list[int | str] = []

        self.enabled_extensions: list[str] = []
        self.initial_cogs: list[str] = []

        # Needed for Discord.py command mentions
        self.all_dpy_commands = None

    @property
    def cmd_count(self) -> int:
        """The number of loaded application commands, including subcommands."""
        if PYCORD:
            cmds = [
                cmd
                for cmd in self.walk_application_commands()
                if type(cmd) is not discord.SlashCommandGroup
            ]
        else:
            cmds = []
            for cog in self.cogs.values():
                for cmd in cog.walk_app_commands():
                    cmds.append(cmd)

        return len(cmds)

    async def get_application_context(self, interaction: discord.Interaction, cls=EzContext):
        """A custom application command context for Pycord."""
        return await super().get_application_context(interaction, cls=cls)

    def _send_cog_log(
        self,
        custom_log_level: str | None,
        log_format: str,
        color: str | None,
    ):
        if custom_log_level:
            custom_log(custom_log_level, log_format, color=color, level=logging.INFO)
        else:
            self.logger.info(log_format)

    def _cog_log(
        self,
        cog_name: str,
        custom_log_level: str | None,
        log_format: CogLog | str | None,
        directory: str,
        color: str | None = None,
    ):
        """Sends a log message for a loaded cog."""

        if not log_format or "{sum}" in log_format:
            return

        log_format = log_format.replace("{cog}", cog_name)

        dot = "." if directory else ""
        log_format = log_format.replace("{path}", f"{directory}{dot}{cog_name}")
        log_format = log_format.replace("{directory}", f"{directory}")

        self._send_cog_log(custom_log_level, log_format, color=color)

    def _cog_count_log(
        self,
        custom_log_level: str | None,
        log_format: CogLog | str | None,
        count: int,
        color: str | None = None,
        directory: str | None = None,
    ):
        """Sends a log message for the number of loaded cogs in a directory or in total."""

        if not log_format or "{cog}" in log_format or "{path}" in log_format:
            return
        if directory and "{directory}" not in log_format:
            return
        if count == 0:
            return
        if count == 1:
            log_format = log_format.replace("cogs", "cog")

        if directory and "{sum}" in log_format and "{directory}" in log_format:
            log_format = log_format.replace("{sum}", str(count))
            log_format = log_format.replace("{directory}", directory)
        elif not directory and "{sum}" in log_format and "{directory}" not in log_format:
            log_format = log_format.replace("{sum}", str(count))
        else:
            return

        self._send_cog_log(custom_log_level, log_format, color=color)

    def _manage_cogs(
        self,
        *directories: str,
        subdirectories: bool = False,
        ignored_cogs: list[str] | None,
        log: CogLog | str | None = CogLog.default,
        custom_log_level: str | None,
        log_color: str | None,
    ):
        cogs = []

        ignored_cogs = ignored_cogs or []
        if not directories:
            directories = ("cogs",)

        loaded_cogs = 0
        for directory in directories:
            for root, dirs, files in os.walk(directory):
                path = Path(root)
                loaded_dir_cogs = 0
                for filename in files:
                    name = filename[:-3]
                    if (
                        filename.endswith(".py")
                        and not filename.startswith("_")
                        and name not in ignored_cogs
                    ):
                        cogs.append(f"{'.'.join(path.parts)}.{name}")
                        loaded_dir_cogs += 1
                        self._cog_log(
                            f"{name}", custom_log_level, log, ".".join(path.parts[1:]), log_color
                        )
                loaded_cogs += loaded_dir_cogs

                self._cog_count_log(custom_log_level, log, loaded_dir_cogs, log_color, path.stem)
                if not subdirectories:
                    break
        self._cog_count_log(custom_log_level, log, loaded_cogs, log_color)
        return cogs

    def load_cogs(
        self,
        *directories: str,
        subdirectories: bool = False,
        ignored_cogs: list[str] | None = None,
        log: CogLog | str | None = CogLog.default,
        custom_log_level: str | None = "COG",
        log_color: str | None = None,
    ):
        """Load all cogs in the given directories.

        Parameters
        ----------
        *directories:
            Names of the directories to load cogs from.
            Defaults to ``"cogs"``.
        subdirectories:
            Whether to load cogs from subdirectories.
            Defaults to ``False``.
        ignored_cogs:
            A list of cogs to ignore. Defaults to ``None``.
        log:
            The log format for cogs. Defaults to :attr:`.CogLog.default`.
            If this is ``None``, logs will be disabled.
        custom_log_level:
            The name of the custom log level for cogs. Defaults to ``COG``.
        log_color:
            The color to use for cog logs. This will only have an effect if ``custom_log_level`` is enabled.
            If this is ``None``, a default color will be used.
        """

        cogs = self._manage_cogs(
            *directories,
            subdirectories=subdirectories,
            ignored_cogs=ignored_cogs,
            log=log,
            custom_log_level=custom_log_level,
            log_color=log_color,
        )
        self.initial_cogs = cogs

        if not DPY:
            for cog in cogs:
                self.load_extension(cog)

    def add_ready_info(
        self,
        name: str,
        value: str | int,
        position: int | None = None,
        color: str | None = None,
    ):
        """Adds an information to the ``on_ready`` message.

        Parameters
        ----------
        name:
            The name of the info to add. If this name already exists, the info will be updated.
        value:
            The value of the info.
        position:
            The position of the info. If this is ``None``, the info will be added at the end.
        color:
            The color of the info. If this is ``None``, a default color will be used.
        """
        self.ready_event_adds[name] = {"value": value, "position": position, "color": color}

    def remove_ready_info(self, *elements: str | int):
        """Removes an information from the ``on_ready`` message.

        Parameters
        ----------
        *elements:
            The names or positions of the infos to remove.
        """
        for element in elements:
            self.ready_event_removes.append(element)

    def ready(
        self,
        *,
        title: str = READY_TITLE,
        style: ReadyEvent = ReadyEvent.default,
        default_info: bool = True,
        new_info: dict | None = None,
        colors: list[str] | None = None,
    ):
        """Print a custom ready message.

        Parameters
        ----------
        title:
            The title of the ready message.
        style:
            The style of the ready message. Defaults to :attr:`.ReadyEvent.default`.
        default_info:
            Whether to include the default information. Defaults to ``True``.
        new_info:
            A dictionary of additional information to include in the ready message.
            Defaults to ``None``.

            .. note::
                Information can also be added with :meth:`.add_ready_info` and removed with
                :meth:`.remove_ready_info`.
        colors:
            A list of colors to use for the ready message. If no colors are given,
            default colors will be used.

            Colors can only be used with :attr:`.ReadyEvent.box_colorful` and all table styles.
        """
        modifications = self.ready_event_adds, self.ready_event_removes
        print_custom_ready(self, title, modifications, style, default_info, new_info, colors)

    async def _ready_event(self):
        """Prints the bot's information when it's ready."""
        await asyncio.sleep(0.1)

        modifications = self.ready_event_adds, self.ready_event_removes
        print_ready(self, self.ready_event, modifications=modifications)

        if DPY:
            self.all_dpy_commands = await self.tree.fetch_commands()

    @staticmethod
    async def _db_setup():
        """Calls the setup method of all registered :class:`.DBHandler` instances."""

        load_dotenv()
        auto_setup = os.getenv("PGAUTOSETUP", "1") == "1"

        if len(PGHandler._auto_setup) != 0:
            await PGHandler()._check_pool()  # make sure that pool is created before setup
            for instance in PGHandler._auto_pool.copy():
                await instance._check_pool()

        if not auto_setup:
            return

        setup_copy = DBHandler._auto_setup.copy() + PGHandler._auto_setup.copy()

        tasks = []
        for instance in setup_copy:
            if hasattr(instance, "setup") and callable(instance.setup):
                tasks.append(instance.setup())

        await asyncio.gather(*tasks)

    async def _check_cog_groups(self):
        """Checks if all cog groups are valid."""
        for cog in self.cogs.values():
            if hasattr(cog, "group") and cog.group:
                if cog.group not in self.cogs.keys():
                    self.logger.warning(
                        f"The cog group '{cog.group}' for cog '{cog.qualified_name}' does not exist."
                    )

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """This overrides the default ``on_error`` event to send an error webhook."""

        if self.error_webhook_url:
            description = f"- **Event:** {event_method}\n```py\n{traceback.format_exc()}```"
            webhook_sent = await self._send_error_webhook(description[:3750])
        else:
            webhook_sent = False

        self.logger.exception(
            f"Error in event **{event_method}** ```{traceback.format_exc(limit=0)}```",
            extra={"webhook_sent": webhook_sent},
        )

    async def _error_event(self, ctx, error: discord.DiscordException):
        """The event that handles application command errors."""
        if type(error) in self.ignored_errors + [ErrorMessageSent]:
            return

        if (
            (PYCORD and type(error) is discord.CheckFailure)
            or (DPY and type(error) is discord.app_commands.CheckFailure)
            or type(error) is commands.CheckFailure
        ):
            if self.error_handler:
                await error_emb(ctx, tr("no_user_perms", use_locale=ctx))
            return

        if isinstance(error, commands.CommandOnCooldown):
            if self.error_handler:
                seconds = round(ctx.command.get_cooldown_retry_after(ctx))
                cooldown_txt = tr("cooldown", dc_timestamp(seconds), use_locale=ctx)
                await error_emb(ctx, cooldown_txt, title=tr("cooldown_title", use_locale=ctx))

        elif isinstance(error, checks.BotMissingPermissions):
            if self.error_handler:
                perms = "\n".join(error.missing_permissions)
                perm_txt = f"{tr('no_perms', use_locale=ctx)} ```\n{perms}```"
                await error_emb(ctx, perm_txt, title=tr("no_perms_title", use_locale=ctx))

        elif isinstance(error, commands.NotOwner):
            if self.error_handler:
                await error_emb(ctx, tr("no_user_perms", use_locale=ctx))

        else:
            if "original" in error.__dict__ and not self.full_error_traceback:
                original_error = error.__dict__["original"]
                error_msg = f"{original_error.__class__.__name__}: {error.__cause__}"
                error = original_error
            else:
                error_msg = f"{error}"

            if self.error_handler:
                error_txt = f"{tr('error', f'```{error_msg}```', use_locale=ctx)}"
                try:
                    await error_emb(ctx, error_txt, title=tr("error_title", use_locale=ctx))
                except discord.HTTPException as e:
                    # ignore invalid interaction error, probably took too long to respond
                    if e.code != 10062:
                        self.logger.error("Could not send error message to user", exc_info=e)

            webhook_sent = False
            if self.error_webhook_url:
                description = get_error_text(ctx, error)
                webhook_sent = await self._send_error_webhook(description)

            self.logger.exception(
                f"Error while executing **/{ctx.command.qualified_name}** ```{error_msg}```",
                exc_info=error,
                extra={"webhook_sent": webhook_sent},
            )

    async def _send_error_webhook(self, description):
        webhook_sent = False
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                self.error_webhook_url, session=session, bot_token=self.http.token
            )

            embed = discord.Embed(
                title="Error Report",
                description=description,
                color=discord.Color.red(),
            )
            try:
                await webhook.send(
                    embed=embed,
                    username=f"{self.user.name} Error Report",
                    avatar_url=self.user.display_avatar.url,
                )
            except discord.HTTPException:
                self.logger.error(
                    "Error while sending error report to webhook. "
                    "Please check if the URL is correct."
                )
            else:
                webhook_sent = True

        return webhook_sent

    def get_cmd(self, name: str, bold: bool = True) -> str:
        """Helper method to get a command mention. Returns a string if the command was not found.

        Parameters
        ----------
        name:
            The name of the command to get.
        bold:
            Whether to bold the command name. Defaults to ``True``.
        """
        default = f"**/{name}**" if bold else f"/{name}"

        if not DPY:
            cmd = self.get_application_command(name)
            if cmd is None:
                return default
            return cmd.mention

        else:
            if not self.all_dpy_commands:
                return default

            for c in self.all_dpy_commands:
                if c.name == name:
                    return c.mention

            return default

    def add_help_command(
        self,
        *,
        style: HelpStyle = HelpStyle.default,
        embed: discord.Embed | None = None,
        show_categories: bool = True,
        show_description: bool = True,
        show_cmd_count: bool = False,
        timeout: int | None = None,
        ephemeral: bool = True,
        author_only: bool = True,
        guild_only: bool = False,
        buttons: list[discord.Button] | None = None,
        title_format: str = "{emoji} - {name}",
        description_format: str = "{description}",
        permission_check: bool = False,
        **kwargs: Callable | str,
    ):
        """Add a help command that uses a select menu to group commands by cogs.

        If you use :class:`Cog`, you can pass in emojis to use for the select menu.

        .. hint::
            Title and description can be formatted with the following placeholders:

            - ``{emoji}`` - The emoji of the cog.
            - ``{name}`` - The name of the cog.
            - ``{description}`` - The description of the cog.

        Parameters
        ----------
        style:
            The style to use for the help command. Defaults to :attr:`.HelpStyle.default`.
        embed:
            The embed to use for the help command. If this is ``None``, a default
            embed will be used.
            All template variables that are listed in :meth:`ezcord.emb.set_embed_templates`
            can be used here.
        show_categories:
            Whether to display the categories of the help command front page. Defaults to ``True``.
        show_description:
            Whether to display the description in each category page. Defaults to ``True``.
        show_cmd_count:
            Whether to display the command count of each category in the select menu.
            Defaults to ``False``.
        timeout:
            The timeout for the select menu. Defaults to ``None``.
        ephemeral:
            Whether the help command should be ephemeral. Defaults to ``True``.
        author_only:
            Whether the help command should only be visible to the author. Defaults to ``True``.
            This only works if ``ephemeral`` is ``False``.
        guild_only:
            Whether the help command should only be visible in guilds. Defaults to ``False``.
        buttons:
            A list of buttons to add to the help command. Defaults to ``None``.
        title_format:
            The title format of each category.
        description_format:
            The description format of each category.
        permission_check:
            Whether to check for permissions before showing a command. Defaults to ``True``.
        **kwargs:
            Additional variables to use in the help command. This can either be a string value or
            a callable that returns a string value.
        """

        if buttons is None:
            buttons = []
        for button in buttons:
            if not isinstance(button, discord.ui.Button):
                raise TypeError(f"Button must be of type 'Button', not {type(button)}.")

        self.help = _CustomHelp(
            style,
            embed,
            show_categories,
            show_description,
            show_cmd_count,
            timeout,
            ephemeral,
            author_only,
            guild_only,
            buttons,
            title_format,
            description_format,
            permission_check,
            kwargs,
        )
        self.enabled_extensions.append("help")
        if not DPY:
            self.load_extension("ezcord.cogs.pyc.help_setup", package="ezcord")

    def add_status_changer(
        self,
        *activities: (
            str
            | discord.Activity
            | discord.Game
            | discord.Streaming
            | discord.CustomActivity
            | list[
                str | discord.Activity | discord.CustomActivity | discord.Game | discord.Streaming
            ]
        ),
        interval: int = 60,
        status: discord.Status = discord.Status.online,
        shuffle: bool = False,
        **kwargs: Callable | str,
    ):
        """Add a status changer that changes the bot's activity every ``interval`` seconds.

        .. note::

            You can use the following variables in status texts:

            - ``{guild_count}`` - The number of guilds the bot is in.
            - ``{user_count}`` - The number of users the bot can see.
            - ``{cmd_count}`` - The number of application commands.

            You can create custom variables by passing in variable names and values
            as ``**kwargs``.

        Parameters
        ----------
        activities:
            Activities to use for the status. Strings will be converted
            to :class:`discord.CustomActivity`.
        interval:
            The interval in seconds to change the status. Defaults to ``60``.
        status:
            The status to use. Defaults to :attr:`discord.Status.online`.
        shuffle:
            Whether to use a random order for the activities. Defaults to ``False``.
        **kwargs:
            Additional variables to use in status texts. This can either be a string value or
            a callable that returns a string value.

        Example
        -------
        .. code-block:: python3

            def get_coins():  # This can also be async
                return 69

            bot.add_status_changer(
                [
                    "{guild_count} Servers",  # Strings will be converted to CustomActivity
                    discord.Game("with {coins} coins")
                ],
                coins=get_coins
            )
        """

        final_acts = []
        for act in activities:
            if isinstance(act, (list, tuple)):
                for list_activity in act:
                    final_acts.append(list_activity)
            else:
                final_acts.append(act)

        self.status_changer = _StatusChanger(
            final_acts,
            interval,
            status,
            shuffle,
            kwargs,
        )
        self.enabled_extensions.append("status_changer")
        if not DPY:
            self.load_extension("ezcord.cogs.pyc.status_changer_setup", package="ezcord")

    def add_blacklist(
        self,
        admin_server_ids: list[int],
        *,
        db_path: str = "blacklist.db",
        db_name: str = "blacklist",
        raise_error: bool = False,
        owner_only: bool = True,
        disabled_commands: list[EzConfig.BLACKLIST_COMMANDS] | None = None,
        **kwargs: Callable,
    ):
        """Add a blacklist that bans users from using the bot. This should be called
        before the ``on_ready`` event.

        Parameters
        ----------
        admin_server_ids:
            A list of server IDs. Admins on these servers will be able to see the admin commands.
        db_path:
            The path to the database file.
        db_name:
            The name of the database.
        raise_error:
            Whether to raise :class:`.errors.Blacklisted` error in case a blacklisted user uses
            the bot. If this is ``False``, a default message will be sent to the user.

            .. note::

                This can be used to handle the error in your own error handler.

        owner_only:
            Whether the blacklist can only be managed by the bot owner. Defaults to ``True``.
        disabled_commands:
            A list of command names to disable. Defaults to ``None``.
        **kwargs:
            Overwrites for the default blacklist commands. This can be used to change the
            default commands behavior.
        """

        if disabled_commands is None:
            disabled_commands = []

        for name, func in kwargs.items():
            if name not in EzConfig.BLACKLIST_COMMANDS.__args__:  # type: ignore
                raise ValueError(
                    f"Invalid blacklist command name '{name}'. "
                    f"Possible values are: {EzConfig.BLACKLIST_COMMANDS.__args__}."  # type: ignore
                )

            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f"Blacklist command overwrite `{name}` must be async.")

        EzConfig.blacklist = Blacklist(
            db_path,
            db_name,
            raise_error,
            owner_only,
            disabled_commands,
            overwrites=kwargs,
        )
        EzConfig.admin_guilds = admin_server_ids

        self.enabled_extensions.append("blacklist")
        if not DPY:
            self.load_extension("ezcord.cogs.pyc.blacklist_setup", package="ezcord")

    def localize_commands(
        self, languages: dict[str, dict], default: str = "en-US", cogs: bool = True
    ):
        """
        Localize commands with the given test dictionary. This should be called after the
        commands have been added to the bot, but before they are synced.

        A list of available languages is available here:
        https://discord.com/developers/docs/reference#locales

        This is currently only supported for Pycord.

        Parameters
        ----------
        languages:
            A dictionary with command localizations. An example can be found in the
            :doc:`localization example </examples/localization>`.

            If an ``en`` key is found, the values will be used for both ``en-GB`` and ``en-US``.
        default:
            The default language to use for languages that are not in the dictionary.
            Defaults to ``en-US``.
        cogs:
            Whether to localize the cogs. Defaults to ``True``.
        """
        if "en" in languages:
            en = languages.pop("en")
            languages["en-GB"] = en
            languages["en-US"] = en

        if default == "en":
            default = "en-US"

        I18N.cmd_localizations = languages

        for locale, localizations in languages.items():
            for cmd_name, cmd_localizations in localizations.items():
                if cmd := discord.utils.get(
                    self._pending_application_commands, qualified_name=cmd_name
                ):
                    localize_command(cmd, locale, cmd_localizations, default)

            if cogs and "cogs" in localizations:
                for cog_name, cog in self.cogs.items():
                    localize_cog(cog_name, cog, locale, localizations["cogs"])

    async def setup_hook(self):
        """This is used for Discord.py startup and should not be called manually."""

        for cog in self.initial_cogs:
            await self.load_extension(cog)

        for ext in self.enabled_extensions:
            await self.load_extension(f".cogs.dpy.{ext}_setup", package="ezcord")

    def _run_setup(
        self,
        env_path: str | os.PathLike[str] | None,
        token_var: str,
        token: str | None,
    ):
        if not env_path:
            return token

        load_dotenv(env_path)
        env_token = os.getenv(token_var)
        if token is None and env_token is not None:
            token = env_token

        if not self.error_webhook_url:
            error_webhook_url = os.environ.get("ERROR_WEBHOOK_URL")
            if error_webhook_url is not None:
                self.error_webhook_url = error_webhook_url
                if not self.error_event_added:
                    if DPY:
                        self.tree.on_error = self._error_event
                    else:
                        self.add_listener(self._error_event, "on_application_command_error")

        return token

    def run(
        self,
        token: str | None = None,
        *,
        env_path: str | os.PathLike[str] | None = ".env",
        token_var: str = "TOKEN",
        **kwargs,
    ) -> None:
        """This overrides the default :meth:`discord.Bot.run` method and automatically loads the token
        from the environment.

        Parameters
        ----------
        token:
            The bot token. If this is ``None``, the token will be loaded from the environment.
        env_path:
            The path to the environment file. Defaults to ``.env``. If this is ``None``, environment
            variables are not loaded automatically.
        token_var:
            The name of the token variable in the environment file. Defaults to ``TOKEN``.
        **kwargs:
            Additional keyword arguments for :meth:`discord.Bot.run`.
        """
        token = self._run_setup(env_path, token_var, token)
        super().run(token, **kwargs)

    async def start(
        self,
        token: str | None = None,
        *,
        env_path: str | os.PathLike[str] | None = ".env",
        token_var: str = "TOKEN",
        **kwargs,
    ) -> None:
        """This overrides the default :meth:`discord.Bot.start` method and automatically loads the token
        from the environment.

        Parameters
        ----------
        token:
            The bot token. If this is ``None``, the token will be loaded from the environment.
        env_path:
            The path to the environment file. Defaults to ``.env``. If this is ``None``, environment
            variables are not loaded automatically.
        token_var:
            The name of the token variable in the environment file. Defaults to ``TOKEN``.
        **kwargs:
            Additional keyword arguments for :meth:`discord.Bot.start`.
        """
        token = self._run_setup(env_path, token_var, token)
        await super().start(token, **kwargs)


class PrefixBot(Bot, commands.Bot):
    """A subclass of :class:`discord.ext.commands.Bot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with prefix commands.
    This is only needed for Pycord.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BridgeBot(Bot, bridge.Bot):
    """A subclass of :class:`discord.ext.bridge.Bot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with bridge commands.
    This is only needed for Pycord.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AutoShardedBot(Bot, AutoShardedBot):  # type: ignore
    """A subclass of :class:`discord.AutoShardedBot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with an auto-sharded bot.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class _CogMeta(CogMeta):
    """A metaclass for cogs that adds an ``emoji`` attribute."""

    def __new__(cls, *args, **kwargs) -> CogMeta:
        name, bases, attrs = args
        attrs["emoji"] = kwargs.pop("emoji", None)
        attrs["group"] = kwargs.pop("group", None)
        attrs["hidden"] = kwargs.pop("hidden", False)
        return super().__new__(cls, *args, **kwargs)


class Cog(commands.Cog, metaclass=_CogMeta):
    """This can be used as a base class for all cogs.

    Parameters
    ----------
    bot:
        The bot instance.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot


@dataclass
class _CustomHelp:
    style: HelpStyle
    embed: discord.Embed | None
    show_categories: bool
    show_description: bool
    show_cmd_count: bool
    timeout: int | None
    ephemeral: bool
    author_only: bool
    guild_only: bool
    buttons: list[discord.Button]
    title: str
    description: str
    permission_check: bool
    kwargs: dict[str, Callable | str]


@dataclass
class _StatusChanger:
    activities: list
    interval: int
    status: discord.Status
    shuffle: bool
    kwargs: dict[str, Callable | str]
