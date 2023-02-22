"""
.. warning::
    These utilities are only used by the library itself and
    are **not** meant to be used directly.
"""
import os
import inspect
from typing import Literal
from configparser import ConfigParser
from pathlib import Path

from .translation import *


def plural_de(amount, word, relative=True) -> str:
    """Pluralize a given word (German).

    Parameters
    ----------
    amount: :class:`int`
        The amount to check.
    word: :class:`str`
        The word to pluralize.
    relative: :class:`bool`
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


def plural_en(amount, word) -> str:
    """Pluralize a given word (English).

    Parameters
    ----------
    amount: :class:`int`
        The amount to check.
    word: :class:`str`
        The word to pluralize.
    """
    if amount != 1:
        return f"{word}s"
    return word


def tp(key, amount, *args, relative=True) -> str:
    """Load a string in the selected language and pluralize it.

    Parameters
    ----------
    key: :class:`str`
        The text to load.
    amount: :class:`int`
        The amount to check.
    *args: :class:`str`
        The arguments to format the string with.
    relative: :class:`bool`
        Whether to use relative time. Defaults to ``True``.
    """
    word = t(key, *args)
    lang = get_lang()

    if lang == "de":
        return plural_de(amount, word, relative)
    else:
        return plural_en(amount, word)


def t(key, *args):
    """Load a string in the selected language.

    Parameters
    ----------
    key: :class:`str`
        The text to load.
    *args: :class:`str`
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
