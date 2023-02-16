import os

import discord


class Bot(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_cogs(self, directory: str = "cogs") -> None:
        for filename in os.listdir(f"./{directory}"):
            if filename.endswith(".py"):
                self.load_extension(f'{directory}.{filename[:-3]}')

    async def on_ready(self):
        print(f"{self.user} is online ({discord.__version__})")
