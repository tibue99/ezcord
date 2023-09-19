from collections.abc import Iterable

from .dc_imports import discord

commands = __import__(f"{discord.lib}.ext.commands", fromlist=[""])


try:
    # py-cord
    from discord import CogMeta
    from discord.ext import bridge
    from discord.utils import AutocompleteFunc, V, Values

except ImportError:
    CogMeta = commands.CogMeta
    bridge = commands

    AutocompleteFunc = None
    V = Iterable[str]
    Values = Iterable[str]
