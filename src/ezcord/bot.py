import os
import traceback
from typing import Literal, List, Any

import discord
from discord.ext import commands

from .log import set_log
from .times import dc_timestamp
from .utils import t, set_lang


class Bot(discord.Bot):
    """Bot class that extends from :class:`discord.Bot`.

    Parameters
    ----------
    debug:
        Enable debug logs. Defaults to ``True``.
    log_file:
        Log to file instead of console. Defaults to ``False``.
    error_handler:
        Enable the error handler. Defaults to ``True``.
    error_channel:
        The channel to send error messages to. Defaults to ``None``.

        .. note::
            You need to enable the error handler for the webhook to work.
    ignored_errors:
        A list of error types to ignore. Defaults to ``None``.
    ignored_cogs:
        A list of cogs to ignore. Defaults to ``None``.
    language:
        The language to use for the bot. Defaults to ``en``.
    log_format:
        The log format. Defaults to ``[%(asctime)s] %(levelname)s: %(message)s``.
    time_format:
        The time format. Defaults to ``%Y-%m-%d %H:%M:%S``.
    """
    def __init__(
            self,
            debug: bool = True,
            log_file: bool = False,
            error_handler: bool = True,
            error_channel: int = None,
            ignored_errors: List[Any] = None,
            ignored_cogs: List[str] = None,
            language: Literal["en", "de"] = "en",
            log_format: str = "[%(asctime)s] %(levelname)s: %(message)s",
            time_format: str = "%Y-%m-%d %H:%M:%S",
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.logger = set_log(__name__, debug=debug, file=log_file, log_format=log_format, time_format=time_format)
        self.error_channel = error_channel
        self.ignored_errors = ignored_errors or []
        self.ignored_cogs = ignored_cogs or []
        set_lang(language)

        if error_handler:
            self.add_listener(self._error_event, "on_application_command_error")
        elif error_channel:
            self.logger.warning("You need to enable error_handler for the error_channel to work.")

    def load_cogs(self, directory: str = "cogs", subdirectories: bool = False):
        """Load all cogs in a given directory.

        Parameters
        ----------
        directory:
            Name of the directory to load cogs from.
            Defaults to ``cogs``.
        subdirectories:
            Whether to load cogs from subdirectories.
            Defaults to ``False``.
        """
        if not subdirectories:
            for filename in os.listdir(f"./{directory}"):
                if filename.endswith(".py") and filename not in self.ignored_cogs:
                    self.load_extension(f'{directory}.{filename[:-3]}')
        else:
            for element in os.scandir(directory):
                if element.is_dir():
                    for sub_file in os.scandir(element.path):
                        if sub_file.name.endswith(".py") and sub_file.name not in self.ignored_cogs:
                            self.load_extension(f"{directory}.{element.name}.{sub_file.name[:-3]}")

    async def on_ready(self):
        """Prints the bot's information when it's ready."""
        infos = [
            f"User: {self.user}",
            f"ID: {self.user.id}",
            f"Pycord: {discord.__version__}",
            f"Commands: {len(self.commands):,}",
            f"Guilds: {len(self.guilds):,}",
            f"Latency: {round(self.latency * 1000):,}ms"
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
        if type(error) in self.ignored_errors:
            return

        """The event that handles application command errors."""
        embed = discord.Embed(
            title="Error",
            description=f"{t('error')}: ```{error}```",
            color=discord.Color.red()
        )

        if isinstance(error, commands.CommandOnCooldown):
            seconds = round(ctx.command.get_cooldown_retry_after(ctx))
            embed.title = "Cooldown"
            embed.description = t("cooldown", dc_timestamp(seconds))
            await ctx.respond(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = "\n".join(error.missing_permissions)
            embed.title = t("no_perm_title")
            embed.description = f"{t('no_perm_desc')}" \
                                f"```\n{perms}```"
            await ctx.respond(embed=embed, ephemeral=True)

        else:
            await ctx.respond(embed=embed, ephemeral=True)

            if self.error_channel:
                error_channel = self.get_channel(self.error_channel)
                error_txt = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                guild_txt = f"\n\n`Guild:` {ctx.guild.name} ({ctx.guild.id})" if ctx.guild else ""

                embed = discord.Embed(
                    title="Error Report",
                    description=f"`Command:` /{ctx.command.name}"
                                f"{guild_txt}"
                                f"```{error_txt}```",
                    color=discord.Color.orange()
                )
                await error_channel.send(embed=embed)
            raise error
