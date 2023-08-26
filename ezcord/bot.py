from __future__ import annotations

import asyncio
import logging
import os
import traceback
from pathlib import Path
from typing import Any

import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

from .emb import error as error_emb
from .enums import CogLog, HelpStyle, ReadyEvent
from .internal.dc import CogMeta, bridge, discord
from .logs import DEFAULT_LOG, custom_log, set_log
from .sql import DBHandler
from .times import dc_timestamp

from .internal import (  # isort: skip
    READY_TITLE,
    load_lang,
    print_custom_ready,
    print_ready,
    set_lang,
    t,
    get_error_text,
)


try:
    _main_bot = discord.Bot  # Pycord
except AttributeError:
    _main_bot = commands.Bot


class Bot(_main_bot):  # type: ignore
    """The EzCord bot class. This is a subclass of :class:`discord.Bot`.

    .. hint::

        As this class extends from :class:`discord.Bot`, only slash commands are supported.
        If you want to use prefix commands, use :class:`PrefixBot` instead.

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
        The language to use for user output.

        The default languages are ``en``, ``de``, ``es`` and ``fr``. If you add your own language file as
        described in :doc:`the language example </examples/languages>`, you can use that language as well.
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
        language: str = "en",
        ready_event: ReadyEvent | None = ReadyEvent.default,
        **kwargs,
    ):
        super().__init__(intents=intents, **kwargs)

        if error_webhook_url:
            os.environ.setdefault("ERROR_WEBHOOK_URL", error_webhook_url)

        if debug:
            self.logger = set_log(DEFAULT_LOG)
        else:
            self.logger = logging.getLogger(DEFAULT_LOG)
            self.logger.addHandler(logging.NullHandler())

        self.help: dict = {}
        self.error_handler = error_handler
        self.error_webhook_url = error_webhook_url
        self.ignored_errors = ignored_errors or []
        self.full_error_traceback = full_error_traceback
        load_lang(language)
        set_lang(language) if language != {} else set_lang("en")

        self.error_event_added = False
        if error_handler or error_webhook_url:
            self.error_event_added = True
            self.add_listener(self._error_event, "on_application_command_error")

        self.ready_event = ready_event
        if ready_event:
            self.add_listener(self._ready_event, "on_ready")
        self.add_listener(self._check_cog_groups, "on_ready")
        self.add_listener(self._db_setup, "on_ready")

        self.ready_event_adds: dict = {}
        self.ready_event_removes: list[int | str] = []

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
        subdir: bool = False,
    ):
        """Sends a log message for a loaded cog."""

        if not log_format or "{sum}" in log_format:
            return

        log_format = log_format.replace("{cog}", cog_name)
        log_format = log_format.replace("{path}", f"{directory}.{cog_name}" if subdir else cog_name)
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
        ignored_cogs = ignored_cogs or []
        if not directories:
            directories = ("cogs",)

        loaded_cogs = 0
        for directory in directories:
            path = Path(directory)

            loaded_root_cogs = 0
            for filename in os.listdir(directory):
                name = filename[:-3]
                if filename.endswith(".py") and name not in ignored_cogs:
                    self.load_extension(f"{'.'.join(path.parts)}.{name}")
                    loaded_root_cogs += 1
                    self._cog_log(f"{name}", custom_log_level, log, directory, log_color)

            loaded_cogs += loaded_root_cogs
            self._cog_count_log(custom_log_level, log, loaded_root_cogs, log_color, directory)

            if subdirectories:
                for element in os.scandir(directory):
                    if not element.is_dir():
                        continue

                    loaded_dir_cogs = 0
                    dirname = element.name

                    for sub_file in os.scandir(element.path):
                        name = sub_file.name[:-3]
                        if sub_file.name.endswith(".py") and name not in ignored_cogs:
                            self.load_extension(f"{'.'.join(path.parts)}.{dirname}.{name}")
                            loaded_dir_cogs += 1
                            self._cog_log(
                                f"{name}", custom_log_level, log, dirname, log_color, subdir=True
                            )

                    self._cog_count_log(custom_log_level, log, loaded_dir_cogs, log_color, dirname)
                    loaded_cogs += loaded_dir_cogs

        self._cog_count_log(custom_log_level, log, loaded_cogs, log_color)

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

    @staticmethod
    async def _db_setup():
        """Calls the setup method of all registered :class:`.DBHandler` instances."""
        for instance in DBHandler._auto_setup.values():
            if hasattr(instance, "setup") and callable(instance.setup):
                await instance.setup()

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

    async def _error_event(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        """The event that handles application command errors."""
        if type(error) in self.ignored_errors:
            return

        if isinstance(error, commands.CommandOnCooldown):
            if self.error_handler:
                seconds = round(ctx.command.get_cooldown_retry_after(ctx))
                cooldown_txt = t("cooldown", dc_timestamp(seconds))
                await error_emb(ctx, cooldown_txt, title=t("cooldown_title"))

        elif isinstance(error, commands.BotMissingPermissions):
            if self.error_handler:
                perms = "\n".join(error.missing_permissions)
                perm_txt = f"{t('no_perms')} ```\n{perms}```"
                await error_emb(ctx, perm_txt, title=t("no_perms_title"))

        else:
            if "original" in error.__dict__ and not self.full_error_traceback:
                original_error = error.__dict__["original"]
                error_msg = f"{original_error.__class__.__name__}: {error.__cause__}"
                error = original_error
            else:
                error_msg = f"{error}"

            if self.error_handler:
                error_txt = f"{t('error', f'```{error_msg}```')}"
                try:
                    await error_emb(ctx, error_txt, title=t("error_title"))
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
        cmd = self.get_application_command(name)
        if cmd is None:
            return f"**/{name}**" if bold else f"/{name}"
        return cmd.mention

    def add_help_command(
        self,
        *,
        style: HelpStyle = HelpStyle.embed_description,
        embed: discord.Embed | None = None,
        show_categories: bool = True,
        timeout: int = 500,
        ephemeral: bool = True,
        author_only: bool = True,
        guild_only: bool = True,
        buttons: list[discord.Button] | None = None,
    ):
        """Add a help command that uses a select menu to group commands by cogs.

        If you use :class:`Cog`, you can pass in emojis to use for the select menu.

        Parameters
        ----------
        style:
            The style to use for the help command. Defaults to :attr:`.HelpStyle.default`.
        embed:
            The embed to use for the help command. If this is ``None``, a default
            embed will be used.
        show_categories:
            Whether to display the categories of the help command front page. Defaults to ``True``.
        timeout:
            The timeout for the select menu. Defaults to ``500``.
        ephemeral:
            Whether the help command should be ephemeral. Defaults to ``True``.
        author_only:
            Whether the help command should only be visible to the author. Defaults to ``True``.
            This only works if ``ephemeral`` is ``False``.
        guild_only:
            Whether the help command should only be visible in guilds. Defaults to ``True``.
        buttons:
            A list of buttons to add to the help command. Defaults to ``None``.
        """
        if buttons is None:
            buttons = []
        for button in buttons:
            if not isinstance(button, discord.ui.Button):
                raise TypeError(f"Button must be of type 'Button', not {type(button)}.")

        self.help = {
            "style": style,
            "embed": embed,
            "show_categories": show_categories,
            "timeout": timeout,
            "ephemeral": ephemeral,
            "author_only": author_only,
            "guild_only": guild_only,
            "buttons": buttons,
        }
        self.load_extension(f".cogs.help", package="ezcord")

    def run(
        self,
        token: str | None = None,
        env_path: str | os.PathLike[str] = ".env",
        token_var: str = "TOKEN",
        **kwargs: Any,
    ) -> None:
        """This overrides the default :meth:`discord.Bot.run` method and automatically loads the token.

        Parameters
        ----------
        token:
            The bot token. If this is ``None``, the token will be loaded from the environment.
        env_path:
            The path to the environment file. Defaults to ``.env``.
        token_var:
            The name of the token variable in the environment file. Defaults to ``TOKEN``.
        **kwargs:
            Additional keyword arguments for :meth:`discord.Bot.run`.
        """
        load_dotenv(env_path)
        env_token = os.getenv(token_var)
        if env_token is not None:
            token = env_token

        if not self.error_webhook_url:
            error_webhook_url = os.environ.get("ERROR_WEBHOOK_URL")
            if error_webhook_url is not None:
                self.error_webhook_url = error_webhook_url
                if not self.error_event_added:
                    self.add_listener(self._error_event, "on_application_command_error")

        super().run(token, **kwargs)


class PrefixBot(Bot, commands.Bot):
    """A subclass of :class:`discord.ext.commands.Bot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with prefix commands.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BridgeBot(Bot, bridge.Bot):
    """A subclass of :class:`discord.ext.bridge.Bot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with bridge commands.
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
