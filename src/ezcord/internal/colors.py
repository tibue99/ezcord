from __future__ import annotations

import logging
import re

from colorama import Fore

DEFAULT_COLOR = Fore.MAGENTA

DEFAULT_LOG_COLORS: dict[int, str] = {
    logging.DEBUG: Fore.GREEN,
    logging.INFO: Fore.CYAN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED,
}


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
            f"'{color_string}' is not a valid color string. Use either the colorama library or a string like 'red'."
        )


def replace_second(string: str, substring: str, color: str) -> str:
    """Replaces custom formatters with ansi colors.

    Example
    -------
    >>> replace_second("Hello **world**!", "**", Fore.RED)
    """
    while substring in string:
        string = string.replace(substring, color, 1)
        string = string.replace(substring, Fore.RESET, 1)

    return string


def remove_escapes(string: str) -> str:
    """Removes ansi escape codes from a string."""
    return re.sub(r"\x1b\[[0-9;]*m", "", string)


def replace_dc_format(string: str, color: str | None = None, file: bool = False) -> str:
    """Replaces Discord markdown with ansi colors."""
    if color is None:
        color = DEFAULT_COLOR
    color = get_escape_code(color)

    if file:
        string = string.replace("***", "").replace("**", "")
        string = remove_escapes(string)
    else:
        string = replace_second(string, "***", color)  # text that contains multiple other colors
        string = replace_second(string, "**", color)
    string = re.sub("```.*?```", "", string)  # remove codeblocks
    return string
