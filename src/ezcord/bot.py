import os

import discord

from .log import set_logs


class Bot(discord.Bot):
    def __init__(self, debug: bool = True, log_file: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = set_logs(__name__, debug=debug, file=log_file)

    def load_cogs(self, directory: str = "cogs") -> None:
        for filename in os.listdir(f"./{directory}"):
            if filename.endswith(".py"):
                self.load_extension(f'{directory}.{filename[:-3]}')

    async def on_ready(self):
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
