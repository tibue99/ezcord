try:
    from .dc_imports import discord
except ImportError:
    raise ModuleNotFoundError("No discord library found. Please install a supported library.")

commands = __import__(f"{discord.lib}.ext.commands", fromlist=[""])
tasks = __import__(f"{discord.lib}.ext.tasks", fromlist=[""])


if discord.__title__ == "pycord":
    from discord import CogMeta
    from discord.ext import bridge

    slash_command = discord.slash_command
    checks = commands

else:
    CogMeta = commands.CogMeta
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
