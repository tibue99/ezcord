from __future__ import annotations

import re

from colorama import Fore

DEFAULT_COLOR = Fore.MAGENTA


def get_escape_code(color_string: str | bool) -> str:
    """Converts a color string to an ansi escape code using colorama.

    If the string already is an escape code, it will be returned.
    """
    if not isinstance(color_string, str):
        return DEFAULT_COLOR

    if color_string.startswith("\x1b["):
        return color_string

    try:
        return getattr(Fore, color_string.upper())
    except AttributeError:
        raise ValueError(
            f"{color_string} is not a valid color string. Use either the colorama library or a string like 'red'."
        )


def replace_second(string: str, substring: str, color: str):
    """Replaces custom formatters with ansi colors.

    Example
    -------
    >>> replace_second("Hello **world**!", "**", Fore.RED)
    """
    while substring in string:
        string = string.replace(substring, color, 1)
        string = string.replace(substring, Fore.RESET, 1)

    return string


def replace_dc_format(string: str, color: str | None = None):
    """Replaces Discord markdown with ansi colors."""
    if color is None:
        color = DEFAULT_COLOR
    color = get_escape_code(color)

    string = replace_second(string, "**", color)
    string = re.sub("```.*?```", "", string)  # remove codeblocks
    return string
