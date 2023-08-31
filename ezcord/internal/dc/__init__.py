from collections.abc import Iterable

from .dc_imports import discord

try:
    # py-cord
    from discord.cog import CogMeta
    from discord.commands import slash_command
    from discord.ext import bridge
    from discord.utils import AutocompleteFunc, V, Values

except ImportError:
    # discord.py
    from discord.ext.commands import CogMeta

    slash_command = __import__("discord.app_commands", fromlist=[""])
    bridge = __import__("discord.ext.commands", fromlist=[""])
    AutocompleteFunc = None
    V = Iterable[str]
    Values = Iterable[str]
