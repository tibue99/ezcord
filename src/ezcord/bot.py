from __future__ import annotations

import logging
import os
import traceback
import warnings
from pathlib import Path
from typing import Any, Literal

import aiohttp
import discord
from discord.ext import commands

from .emb import error as error_emb
from .enums import ReadyEvent
from .internal import print_ready, set_lang, t
from .logs import DEFAULT_LOG, custom_log, set_log
from .times import dc_timestamp


class Bot(discord.Bot):
    """The EzCord bot class. This is a subclass of :class:`discord.Bot`.

    .. hint::

        As this class extends from :class:`discord.Bot`, only slash commands are supported.
        If you want to use prefix commands, use :class:`PrefixBot` instead.

    Parameters
    ----------
    intents:
        The intents to use for the bot. Defaults to :meth:`discord.Intents.default()`.
    debug:
        Enable debug logs. Defaults to ``True``.
    error_handler:
        Enable the error handler. Defaults to ``True``.
    error_webhook_url:
        The webhook URL to send error messages to. Defaults to ``None``.

        .. note::
            You need to enable the error handler for the webhook to work.
    ignored_errors:
        A list of error types to ignore. Defaults to ``None``.
    full_error_traceback:
        Whether to send the full error traceback. If this is ``False``,
        only the most recent traceback will be sent. Defaults to ``False``.
    language:
        The language to use for the bot. Defaults to ``en``.
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
        language: Literal["en", "de"] = "en",
        ready_event: ReadyEvent | None = ReadyEvent.default,
        **kwargs,
    ):
        super().__init__(intents=intents, **kwargs)

        if debug:
            self.logger = set_log(DEFAULT_LOG)
        else:
            self.logger = logging.getLogger(DEFAULT_LOG)
            self.logger.addHandler(logging.NullHandler())

        self.error_webhook_url = error_webhook_url
        self.ignored_errors = ignored_errors or []
        self.full_error_traceback = full_error_traceback
        set_lang(language)

        if error_handler:
            self.add_listener(self._error_event, "on_application_command_error")
        elif error_webhook_url:
            warnings.warn("You need to enable the error handler for the webhook to work.")

        self.ready_event = ready_event
        if ready_event:
            self.add_listener(self.on_ready_event, "on_ready")

    def load_cogs(
        self,
        *directories: str,
        subdirectories: bool = False,
        ignored_cogs: list[str] | None = None,
        custom_logs: bool | str = True,
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
        custom_logs:
            Whether to use a custom log format for cogs. Defaults to ``True``.
            You can also pass in a custom color.
        """
        ignored_cogs = ignored_cogs or []
        if not directories:
            directories = ("cogs",)

        for directory in directories:
            path = Path(directory)

            for filename in os.listdir(directory):
                name = filename[:-3]
                if filename.endswith(".py") and name not in ignored_cogs:
                    self.load_extension(f"{'.'.join(path.parts)}.{name}")
                    if custom_logs:
                        custom_log("COG", f"Loaded {name}", color=custom_logs, level=logging.DEBUG)
                    else:
                        self.logger.debug(f"Loaded {name}")

            if subdirectories:
                for element in os.scandir(directory):
                    if not element.is_dir():
                        continue

                    for sub_file in os.scandir(element.path):
                        name = sub_file.name[:-3]
                        if sub_file.name.endswith(".py") and name not in ignored_cogs:
                            self.load_extension(f"{'.'.join(path.parts)}.{element.name}.{name}")
                            if custom_logs:
                                custom_log(
                                    "COG",
                                    f"Loaded {element.name}.{name}",
                                    color=custom_logs,
                                    level=logging.DEBUG,
                                )
                            else:
                                self.logger.debug(f"Loaded {element.name}.{name}")

    async def on_ready_event(self):
        """Prints the bot's information when it's ready."""
        print_ready(self, self.ready_event)

    async def _error_event(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        """The event that handles application command errors."""
        if type(error) in self.ignored_errors:
            return

        if isinstance(error, commands.CommandOnCooldown):
            seconds = round(ctx.command.get_cooldown_retry_after(ctx))
            cooldown_txt = t("cooldown", dc_timestamp(seconds))
            await error_emb(ctx, cooldown_txt, title="Cooldown")

        elif isinstance(error, commands.BotMissingPermissions):
            perms = "\n".join(error.missing_permissions)
            perm_txt = f"{t('no_perm_desc')} ```\n{perms}```"
            await error_emb(ctx, perm_txt, title=t("no_perm_title"))

        else:
            if "original" in error.__dict__ and not self.full_error_traceback:
                original_error = error.__dict__["original"]
                error_msg = f"{original_error.__class__.__name__}: {error.__cause__}"
                error = original_error
            else:
                error_msg = f"{error}"

            error_txt = f"{t('error')}: ```{error_msg}```"
            try:
                await error_emb(ctx, error_txt, title="Error")
            except discord.HTTPException:
                pass

            webhook_sent = False
            if self.error_webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(
                        self.error_webhook_url, session=session, bot_token=self.http.token
                    )
                    error_txt = "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    )
                    guild_txt = (
                        f"\n- **Guild:** {ctx.guild.name} - `{ctx.guild.id}`" if ctx.guild else ""
                    )
                    user_txt = (
                        f"\n- **User:** {ctx.author} - `{ctx.author.id}`" if ctx.author else ""
                    )

                    embed = discord.Embed(
                        title="Error Report",
                        description=f"- **Command:** /{ctx.command.qualified_name}"
                        f"{guild_txt}{user_txt}"
                        f"\n```py\n{error_txt[:3500]}```",
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

            self.logger.exception(
                f"Error while executing **/{ctx.command.qualified_name}** ```{error_msg}```",
                exc_info=error,
                extra={"webhook_sent": webhook_sent},
            )


class PrefixBot(Bot, commands.Bot):
    """A subclass of :class:`discord.ext.commands.Bot` that implements the :class:`Bot` class.

    This class can be used if you want to use EzCord with prefix commands.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
