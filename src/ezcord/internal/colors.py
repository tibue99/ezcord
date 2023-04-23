from __future__ import annotations

from colorama import Fore


def get_escape_code(color_string: str | bool) -> str:
    """Converts a color string to an ansi escape code using colorama.

    If the string already is an escape code, it will be returned.
    """
    if not isinstance(color_string, str):
        return Fore.MAGENTA

    if color_string.startswith("\x1b["):
        return color_string

    try:
        return getattr(Fore, color_string.upper())
    except AttributeError:
        raise ValueError(
            f"{color_string} is not a valid color string. Use either the colorama library or a string like 'red'."
        )
