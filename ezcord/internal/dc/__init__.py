from ...errors import MissingDiscordLibrary

try:
    from .dc_imports import discord
except ImportError:
    raise MissingDiscordLibrary()

commands = __import__(f"{discord.lib}.ext.commands", fromlist=[""])
tasks = __import__(f"{discord.lib}.ext.tasks", fromlist=[""])


try:
    from discord import CogMeta
    from discord.ext import bridge

    slash_command = discord.slash_command
    checks = commands

    discord.lib = "pycord"  # type: ignore

except ImportError:
    CogMeta = commands.CogMeta
    bridge = commands

    try:
        slash_command = discord.app_commands.command
        checks = discord.app_commands.checks

    except AttributeError:
        if discord.__title__ == "nextcord":
            slash_command = discord.slash_command
            checks = commands

        elif discord.__title__ == "disnake":
            slash_command = commands.slash_command
            checks = commands

        discord.lib = discord.__title__  # type: ignore


PYCORD = discord.lib == "pycord"
DPY = discord.lib == "discord"
