"""Some utility functions for Pycord and Python."""

import asyncio
import io
import itertools
import json
from typing import Any

from discord.utils import AutocompleteFunc, V, Values

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


def ez_autocomplete(values: Values) -> AutocompleteFunc:
    """A similar function as :func:`~discord.utils.basic_autocomplete`, but instead of returning
    options starting with the user's value, it returns options containing the user's value.

    Parameters
    ----------
    values: Iterable[str]
        Accepts an iterable of :class:`str`, a callable (sync or async) that takes a single argument
        of :class:`~discord.AutocompleteContext`, or a coroutine. Must resolve to an iterable of :class:`str`.

    """

    async def autocomplete_callback(ctx: discord.AutocompleteContext) -> V:
        _values = values

        if callable(_values):
            _values = _values(ctx)
        if asyncio.iscoroutine(_values):
            _values = await _values

        def check(item: Any) -> bool:
            item = getattr(item, "name", item)
            return str(ctx.value or "").lower() in str(item).lower()

        gen = (val for val in _values if check(val))
        return iter(itertools.islice(gen, 25))

    return autocomplete_callback
