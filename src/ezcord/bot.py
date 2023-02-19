import os

import discord

from .log import set_log


class Bot(discord.Bot):
    """Bot class that extends from :class:`discord.Bot`.

    Parameters
    ----------
    debug: :class:`bool`
        Enable debug logs. Defaults to ``True``.
    log_file: :class:`bool`
        Log to file instead of console. Defaults to ``False``.
    """
    def __init__(
            self,
            debug=True,
            log_file=False,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.logger = set_log(__name__, debug=debug, file=log_file)

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
