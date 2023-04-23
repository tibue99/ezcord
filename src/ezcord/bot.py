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
from .internal.translation import set_lang, t
from .logs import DEFAULT_LOG, custom_log, set_log
from .times import dc_timestamp


class Bot(discord.Bot):
    """Bot class that extends from :class:`discord.Bot`.

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
    language:
        The language to use for the bot. Defaults to ``en``.
    """

    def __init__(
        self,
        intents: discord.Intents = discord.Intents.default(),
        debug: bool = True,
        error_handler: bool = True,
        error_webhook_url: str | None = None,
        ignored_errors: list[Any] | None = None,
        language: Literal["en", "de"] = "en",
        *args,
        **kwargs,
    ):
        super().__init__(intents=intents, *args, **kwargs)

        if debug:
            self.logger = set_log(DEFAULT_LOG)
        else:
            self.logger = logging.getLogger(DEFAULT_LOG)
            self.logger.addHandler(logging.NullHandler())

        self.error_webhook_url = error_webhook_url
        self.ignored_errors = ignored_errors or []
        set_lang(language)

        if error_handler:
            self.add_listener(self._error_event, "on_application_command_error")
        elif error_webhook_url:
            warnings.warn("You need to enable the error handler for the webhook to work.")

        self.add_listener(self.ready_event, "on_ready")

    def load_cogs(
        self,
        *directories: str,
        subdirectories: bool = False,
        ignored_cogs: list[str] | None = None,
        custom_logs: bool = True,
    ):
        """Load all cogs in the given directories.

        Parameters
        ----------
        *directories:
            Names of the directories to load cogs from.
            Defaults to ``cogs``.
        subdirectories:
            Whether to load cogs from subdirectories.
            Defaults to ``False``.
        ignored_cogs:
            A list of cogs to ignore. Defaults to ``None``.
        custom_logs:
            Whether to use a custom logs format for cogs. Defaults to ``True``.
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
                        custom_log("COG", f"Loaded {name}")
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
                                custom_log("COG", f"Loaded {element.name}.{name}")
                            else:
                                self.logger.debug(f"Loaded {element.name}.{name}")

    async def ready_event(self):
        """Prints the bot's information when it's ready."""
        infos = [
            f"User:     {self.user}",
            f"ID:       {self.user.id}",
            f"Pycord:   {discord.__version__}",
            f"Commands: {len(self.commands):,}",
            f"Guilds:   {len(self.guilds):,}",
            f"Latency:  {round(self.latency * 1000):,}ms",
        ]

        longest = max([str(i) for i in infos], key=len)
        formatter = f"<{len(longest)}"

        start_txt = "Bot is online!"
        start_txt += f"\n╔{(len(longest) + 2) * '═'}╗\n"
        for thing in infos:
            start_txt += f"║ {thing:{formatter}} ║\n"
        start_txt += f"╚{(len(longest) + 2) * '═'}╝"
        self.logger.info(start_txt)

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
            error_txt = f"{t('error')}: ```{error}```"
            try:
                await error_emb(ctx, error_txt, title="Error")
            except discord.HTTPException:
                raise error

            if self.error_webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(
                        self.error_webhook_url, session=session, bot_token=self.http.token
                    )
                    error_txt = "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    )
                    guild_txt = (
                        f"\n\n`Guild:` {ctx.guild.name} ({ctx.guild.id})" if ctx.guild else ""
                    )
                    user_txt = f"\n\n`User:` {ctx.author} ({ctx.author.id})" if ctx.author else ""

                    embed = discord.Embed(
                        title="Error Report",
                        description=f"`Command:` /{ctx.command.name}"
                        f"{guild_txt}{user_txt}"
                        f"```{error_txt[:3500]}```",
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
                            "Please check if you the URL is correct."
                        )
            self.logger.exception(f"Error while executing /{ctx.command.name}", exc_info=error)
