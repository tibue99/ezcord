"""Some utility functions for Pycord and Python."""

import io
import json

from .internal.dc import discord


def create_json_file(
    dictionary: dict, filename: str = "data.json", indent: int = 2, **kwargs
) -> discord.File:
    """Create a :class:`discord.File` object from a dictionary.

    Parameters
    ----------
    dictionary:
        The dictionary to convert to a JSON file.
    filename:
        The filename to use for the JSON file.
    indent:
        The indent to use for the JSON file.
    **kwargs:
        Keyword arguments for :class:`discord.File`.

    Returns
    -------
    :class:`discord.File`
    """
    content = json.dumps(dictionary, indent=indent).encode()
    return discord.File(io.BytesIO(content), filename=filename, **kwargs)


def create_text_file(text: str, filename: str = "data.txt", **kwargs) -> discord.File:
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


def create_html_file(html: str, filename: str = "data.html", **kwargs) -> discord.File:
    """Create a :class:`discord.File` object from an HTML string.

    Parameters
    ----------
    html:
        The HTML string to convert to an HTML file.
    filename:
        The filename to use for the HTML file.
    **kwargs:
        Keyword arguments for :class:`discord.File`.

    Returns
    -------
    :class:`discord.File`
    """
    return create_text_file(html, filename, **kwargs)
