import os
import traceback

import discord
from discord.ext import commands
import aiohttp

from .log import set_log
from .times import convert_time


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
        The webhook URL to send error messages to.
    """
    def __init__(
            self,
            debug=True,
            log_file=False,
            error_handler=True,
            error_webhook_url=None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.logger = set_log(__name__, debug=debug, file=log_file)
        self.error_webhook_url = error_webhook_url

        if error_handler:
            self.add_listener(self.error_event, "on_application_command_error")
        elif error_webhook_url:
            self.logger.warning("You need to enable error_handler for the webhook to work.")

    def load_cogs(self, directory="cogs"):
        """Load all cogs in a given directory.

        Parameters
        ----------
        directory: :class:`str`
            Name of the directory to load cogs from.
            Defaults to ``cogs``.
        """
        for filename in os.listdir(f"./{directory}"):
            if filename.endswith(".py"):
                self.load_extension(f'{directory}.{filename[:-3]}')

    async def on_ready(self):
        """
        Prints the bot's information when it's ready.
        """
        infos = [
            f"Pycord: {discord.__version__}",
            f"User: {self.user}",
            f"ID: {self.user.id}",
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

    async def error_event(self, ctx, error):
        """The event that handles application command errors."""
        embed = discord.Embed(
            title="Error",
            description=f"The following error occurred: ```{error}```",
            color=discord.Color.red()
        )

        if isinstance(error, commands.CommandOnCooldown):
            seconds = ctx.command.get_cooldown_retry_after(ctx)
            embed.description = f"Try again in `{convert_time(seconds)}`."
            await ctx.respond(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = "\n".join(error.missing_permissions)
            embed.title = "Missing permission"
            embed.description = f"I'm missing the following permissions to execute this command." \
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
