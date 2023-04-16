"""Internal language utilities for the library."""

import inspect
import os
from configparser import ConfigParser
from functools import cache
from pathlib import Path
from typing import Literal

from .languages import *


def plural_de(amount: int, word: str, relative: bool = True) -> str:
    """Pluralize a given word (German).

    Parameters
    ----------
    amount:
        The amount to check.
    word:
        The word to pluralize.
    relative:
        Whether to use relative time. Defaults to ``True``.

    Examples
    --------
    >>> plural_de(1, "Tag")
    'Tag'
    >>> plural_de(2, "Tag")  # Relative: "Seit 5 Tagen"
    'Tagen'
    >>> plural_de(2, "Tag", relative=False)  # Not relative: "5 Tage"
    'Tage'
    """
    if amount != 1:
        if not word.endswith("e"):
            word += "e"

        if relative:
            return f"{word}n"

    return word


def plural_en(amount: int, word: str) -> str:
    """Pluralize a given word (English).

    Parameters
    ----------
    amount:
        The amount to check.
    word:
        The word to pluralize.

    Returns
    -------
    :class:`str`
        The pluralized word.
    """
    if amount != 1:
        return f"{word}s"
    return word


def tp(key: str, amount: int, *args: str, relative: bool = True) -> str:
    """Load a string in the selected language and pluralize it.

    Parameters
    ----------
    key:
        The text to load.
    amount:
        The amount to check.
    *args:
        The arguments to format the string with.
    relative:
        Whether to use relative time. Defaults to ``True``.
    """
    word = t(key, *args)
    lang = get_lang()

    if lang == "de":
        return plural_de(amount, word, relative)
    else:
        return plural_en(amount, word)


def t(key: str, *args: str):
    """Load a string in the selected language.

    Parameters
    ----------
    key:
        The text to load.
    *args:
        The arguments to format the string with.
    """
    n = 1
    origin_file = Path(inspect.stack()[n].filename).stem

    while origin_file == Path(__file__).stem:
        n += 1
        origin_file = Path(inspect.stack()[n].filename).stem

    lang = get_lang()

    if lang == "de":
        return de[origin_file][key].format(*args)
    else:
        return en[origin_file][key].format(*args)


@cache
def get_lang():
    """Get the language from the config file."""
    parent = Path(__file__).parent.absolute()
    config = ConfigParser()
    config.read(os.path.join(parent, "config.ini"))

    return config["DEFAULT"]["lang"]


def set_lang(lang: Literal["en", "de"]):
    """Set the language in the config file.

    Parameters
    ----------
    lang:
        The language to set.
    """
    parent = Path(__file__).parent.absolute()
    config = ConfigParser()
    config["DEFAULT"] = {"lang": lang}

    with open(os.path.join(parent, "config.ini"), "w") as f:
        config.write(f)
