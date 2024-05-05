"""Some utility functions for Discord and Python."""

from __future__ import annotations

import asyncio
import fnmatch
import io
import itertools
import json
import os
import random
import re
from pathlib import Path
from typing import Any

from .errors import ChannelNotFound, InvalidFormat, MessageNotFound, MissingPermission
from .internal import get_locale
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


def codeblock(
    content: int | str,
    *,
    lang: str = "yaml",
    unit: str = "",
    interaction: discord.Interaction | None = None,
) -> str:
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
    interaction:
        The interaction to get the language from. Defaults to ``None``.
        If not provided, the language will be set to the default language.
        The language will determine how large numbers are formatted.
    """

    if isinstance(content, int):
        number = f"{content:,}"
        if get_locale(interaction) == "de":
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


def count_lines(
    directory: str | None = None,
    *,
    count_empty_lines: bool = True,
    include_hidden: bool = False,
    ignored_dirs: list[str] | None = None,
    ignored_files: list[str] | None = None,
) -> int:
    """Counts the total amount of lines in all Python files in the given directory.

    Parameters
    ----------
    directory:
        The directory to count the lines in. Defaults to the current working directory.
    count_empty_lines:
        Whether to count empty lines. Defaults to ``True``.
    include_hidden:
        Whether to include directories starting with a dot. Defaults to ``False``.
    ignored_dirs:
        A list of directories to ignore. By default, venv folders and folders starting with a dot
        are ignored.
    ignored_files:
        A list of file patterns to ignore.
    """
    if directory is None:
        directory = os.getcwd()
    if ignored_dirs is None:
        ignored_dirs = []
    if ignored_files is None:
        ignored_files = []

    total_lines = 0
    for root, _, files in os.walk(directory):
        if not include_hidden and Path(root).parts[-1].startswith("."):
            ignored_dirs.append(root)
        if "pyvenv.cfg" in files:  # ignore venv folders
            ignored_dirs.append(root)

        if any([True for pattern in ignored_dirs if pattern in str(Path(root))]):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            if any([True for pat in ignored_files if fnmatch.fnmatch(file, pat)]):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, errors="ignore") as f:
                for line in f:
                    if not count_empty_lines and line.strip() == "":
                        continue
                    total_lines += 1

    return total_lines


async def load_message(
    obj: discord.Guild | discord.Bot, message_url: str, error: bool = False
) -> discord.Message | None:
    """Get a message from a message URL.

    Parameters
    ----------
    obj:
        The object to use to fetch the message.
    message_url:
        The URL of the message.
    error:
        Whether to raise an error if the message couldn't be found. If this is ``False``,
        the function will return ``None`` if the message couldn't be found. Defaults to ``False``.

    Raises
    ------
    InvalidFormat
        The message URL is invalid.
    MissingPermission
        The bot does not have permissions to access the channel.
    ChannelNotFound
        The channel was not found.
    MessageNotFound
        The message couldn't be found in the given channel, perhaps it was deleted.
    """
    pattern = r"channels\/(\d+)\/(\d+)\/(\d+)"  # /channels/guild_id/channel_id/message_id
    matches = re.search(pattern, message_url)

    if not matches or len(matches.groups()) != 3:
        if error:
            raise InvalidFormat("The message URL is invalid.")
        return None

    _, channel_id, message_id = matches.groups()

    try:
        channel = await discord.utils.get_or_fetch(obj, "channel", channel_id)
    except discord.Forbidden:
        if error:
            raise MissingPermission("The bot does not have permissions to access the channel.")
        return None
    except discord.NotFound:
        if error:
            raise ChannelNotFound("The channel was not found.")
        return None

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        if error:
            raise MessageNotFound(
                "The message couldn't be found in the given channel, perhaps it was deleted."
            )
        return None

    return message
