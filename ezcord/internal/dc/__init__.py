class NoDiscordLibFound:
    def __init__(self, *args, **kwargs):
        raise ModuleNotFoundError("No discord library found. Please install a supported library.")


class FakeDiscord:
    """A fake class that is used when EzCord is used without a supported Discord library."""

    DiscordException = Exception
    CogMeta = type

    def __getattr__(self, name):
        if name in (
            "ApplicationContext",
            "AutoShardedBot",
            "Bot",
            "Cog",
            "Embed",
            "Interaction",
            "Modal",
            "View",
        ):
            return NoDiscordLibFound

        return FakeDiscord()

    def __call__(self, *args, **kwargs):
        pass


try:
    from .dc_imports import discord

    commands = __import__(f"{discord.lib}.ext.commands", fromlist=[""])
    tasks = __import__(f"{discord.lib}.ext.tasks", fromlist=[""])

except ImportError:
    # EzCord is used without a supported Discord library
    discord = commands = FakeDiscord()  # type: ignore
    tasks, checks = None, commands  # type: ignore


if discord.__title__ == "pycord":
    from discord import AutoShardedBot, CogMeta
    from discord.ext import bridge

    slash_command = discord.slash_command
    checks = commands

else:
    CogMeta = commands.CogMeta
    AutoShardedBot = commands.AutoShardedBot
    bridge = commands

    if discord.__title__ == "discord":
        slash_command = discord.app_commands.command
        checks = discord.app_commands.checks

    elif discord.__title__ == "nextcord":
        slash_command = discord.slash_command
        checks = commands

    elif discord.__title__ == "disnake":
        slash_command = commands.slash_command
        checks = commands


discord.lib = discord.__title__  # type: ignore


PYCORD = discord.lib == "pycord"
DPY = discord.lib == "discord"
