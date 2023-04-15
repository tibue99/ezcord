"""Some utility functions for Pycord and Python."""

import io
import json
from typing import Dict

import discord


def create_json_file(dictionary: Dict, filename: str = "data.json", **kwargs):
    """Create a :class:`discord.File` object from a dictionary.

    Parameters
    ----------
    dictionary:
        The dictionary to convert to a JSON file.
    filename:
        The filename to use for the JSON file.
    **kwargs:
        Keyword arguments for :class:`discord.File`.

    Returns
    -------
    :class:`discord.File`
    """
    content = json.dumps(dictionary, indent=2).encode()
    file = discord.File(io.BytesIO(content), filename=filename, **kwargs)
    return file


def create_text_file(text: str, filename: str = "data.txt", **kwargs):
    """Create a :class:`discord.File` object from a string.

    Parameters
    ----------
    text:
        The string to convert to a text file.
    filename:
        The filename to use for the text file.
    **kwargs:
        Keyword arguments for :class:`discord.File`.

    Returns
    -------
    :class:`discord.File`
    """
    return discord.File(io.BytesIO(text.encode()), filename=filename, **kwargs)
