import os
import traceback
from typing import Literal, List, Any

import discord
from discord.ext import commands
import aiohttp

from .log import set_log
from .times import convert_time
from .utils import t, set_lang


class Bot(discord.Bot):
    """Bot class that extends from :class:`discord.Bot`.

    Parameters
    ----------
    debug: :class:`bool`
        Enable debug logs. Defaults to ``True``.
    log_file: :class:`bool`
        Log to file instead of console. Defaults to ``False``.
    error_handler: :class:`bool`
        Enable the error handler. Defaults to ``True``.
    error_webhook_url: :class:`str`
        The webhook URL to send error messages to. Defaults to ``None``.
    ignored_errors: :class:`list`
        A list of error types to ignore. Defaults to ``None``.
    ignored_cogs: :class:`list`
        A list of cogs to ignore. Defaults to ``None``.
    language: :class:`str`
        The language to use for the bot. Defaults to ``en``.
    log_format: :class:`str`
        The log format. Defaults to ``[%(asctime)s] %(levelname)s: %(message)s``.
    time_format: :class:`str`
        The time format. Defaults to ``%Y-%m-%d %H:%M:%S``.
        .. note::
            Supported languages: ``en``, ``de``
    """
    def __init__(
            self,
            debug: bool = True,
            log_file: bool = False,
            error_handler: bool = True,
            error_webhook_url: str = None,
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
        self.error_webhook_url = error_webhook_url
        self.ignored_errors = ignored_errors or []
        self.ignored_cogs = ignored_cogs or []
        set_lang(language)

        if error_handler:
            self.add_listener(self._error_event, "on_application_command_error")
        elif error_webhook_url:
            self.logger.warning("You need to enable error_handler for the webhook to work.")

    def load_cogs(self, directory: str = "cogs", subdirectories: bool = False):
        """Load all cogs in a given directory.

        Parameters
        ----------
        directory: :class:`str`
            Name of the directory to load cogs from.
            Defaults to ``cogs``.
        subdirectories: :class:`bool`
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
            embed.description = t("cooldown", convert_time(seconds))
            await ctx.respond(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = "\n".join(error.missing_permissions)
            embed.title = t("no_perm_title")
            embed.description = f"{t('no_perm_desc')}" \
                                f"```\n{perms}```"
            await ctx.respond(embed=embed, ephemeral=True)

        else:
            await ctx.respond(embed=embed, ephemeral=True)

            if self.error_webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(
                        self.error_webhook_url,
                        session=session,
                        bot_token=self.http.token
                    )
                    error_txt = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                    guild_txt = f"\n\n`Guild:` {ctx.guild.name} ({ctx.guild.id})" if ctx.guild else ""

                    embed = discord.Embed(
                        title="Error Report",
                        description=f"`Command:` /{ctx.command.name}"
                                    f"{guild_txt}"
                                    f"```{error_txt}```",
                        color=discord.Color.orange()
                    )
                    await webhook.send(embed=embed)
            raise error
