"""Some utility functions for Discord and Python."""

from __future__ import annotations

import asyncio
import io
import itertools
import json
import random
from typing import Any

from .internal import get_lang
from .internal.dc import discord


def create_json_file(
    dictionary: dict,
    filename: str = "data.json",
    *,
    indent: int = 2,
    description: str | None = None,
    spoiler: bool = False,
    **kwargs,
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
    description:
        The description to use for the discord file.
    spoiler:
        Whether the Discord file should be a spoiler.
    **kwargs:
        Additional keyword arguments for :py:func:`json.dumps`.

    Returns
    -------
    :class:`discord.File`
    """
    content = json.dumps(dictionary, indent=indent, **kwargs).encode()
    return discord.File(
        io.BytesIO(content),
        filename=filename,
        description=description,
        spoiler=spoiler,
    )


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


def random_avatar() -> str:
    """Returns the URL of a random default avatar."""

    return f"https://cdn.discordapp.com/embed/avatars/{random.randint(0, 5)}.png"


def codeblock(content: int | str, *, lang: str = "yaml", unit: str = ""):
    """Returns a codeblock with the given content.

    Parameters
    ----------
    content:
        The content of the codeblock. If the content is an integer, it will be
        formatted with commas (or dots if the language is German).
    lang:
        The language of the codeblock. Defaults to ``yaml``.
    unit:
        The text to display after the given content. This is only used if the content is an integer.
    """

    if isinstance(content, int):
        number = f"{content:,}"
        if get_lang() == "de":
            number = number.replace(",", ".")
        block = f"```{lang}\n{number}"
        if unit:
            block += f" {unit}"
        block += "```"
        return block

    return f"```{lang}\n{content}```"


def ez_autocomplete(values):
    """A similar function as :func:`~discord.utils.basic_autocomplete`, but instead of returning
    options starting with the user's value, it returns options containing the user's value.

    Parameters
    ----------
    values: Iterable[str]
        Accepts an iterable of :class:`str`, a callable (sync or async) that takes a single argument
        of :class:`~discord.AutocompleteContext`, or a coroutine. Must resolve to an iterable of :class:`str`.
    """

    async def autocomplete_callback(ctx):
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
