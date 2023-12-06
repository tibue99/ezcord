from __future__ import annotations

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

    slash_command = discord.commands.slash_command
    checks = commands

    INTERACTION = discord.Interaction | discord.ApplicationContext

    discord.lib = "pycord"  # type: ignore

except ImportError:
    CogMeta = commands.CogMeta
    bridge = commands

    slash_command = discord.app_commands.command
    checks = discord.app_commands.checks

    INTERACTION = discord.Interaction

PYCORD = discord.lib == "pycord"
