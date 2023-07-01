from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from discord.utils import format_dt, utcnow

from .internal import tp


def set_utc(dt: datetime) -> datetime:
    """Set the timezone of a datetime object to UTC.

    Parameters
    ----------
    dt:
        The datetime object to set the timezone of.

    Returns
    -------
    :class:`datetime.datetime`
    """
    return dt.replace(tzinfo=timezone.utc)


def convert_time(seconds: int | float, relative: bool = True) -> str:
    """Convert seconds to a human-readable time.

    Parameters
    ----------
    seconds:
        The amount of seconds to convert.
    relative:
        Whether to use relative time. Defaults to ``True``.

        .. hint::
            This is only needed for German translation and will
            not have any effect if the language is set to English.

            >>> convert_time(450000, relative=True)  # Relative: Seit 5 Tagen
            '5 Tagen'
            >>> convert_time(450000, relative=False)  # Not relative: 5 Tage
            '5 Tage'

    Returns
    -------
    :class:`str`
        A human-readable time.
    """
    if seconds < 60:
        return f"{round(seconds)} {tp('sec', round(seconds))}"
    minutes = seconds / 60
    if minutes < 60:
        return f"{round(minutes)} {tp('min', round(minutes))}"
    hours = minutes / 60
    if hours < 24:
        return f"{round(hours)} {tp('hour', round(hours))}"
    days = hours / 24
    return f"{round(days)} {tp('day', round(days), relative=relative)}"


def convert_dt(dt: datetime | timedelta, relative: bool = True) -> str:
    """Convert :class:`datetime` or :class:`timedelta` to a human-readable time.

    This function calls :func:`convert_time`.

    Parameters
    ----------
    dt:
        The datetime or timedelta object to convert.
    relative:
        Whether to use relative time. Defaults to ``True``.

    Returns
    -------
    :class:`str`
        A human-readable time.
    """
    if isinstance(dt, timedelta):
        return convert_time(abs(dt.total_seconds()), relative)

    if isinstance(dt, datetime):
        return convert_time(abs((dt - utcnow()).total_seconds()), relative)


def dc_timestamp(
    seconds: int | float, style: Literal["t", "T", "d", "D", "f", "F", "R"] = "R"
) -> str:
    """Convert seconds to a Discord timestamp.

    Parameters
    ----------
    seconds:
        The amount of seconds to convert.
    style: :class:`str`
        The style of the timestamp. Defaults to ``R``.
        For more information, see :func:`discord.utils.format_dt`.

    Returns
    -------
    :class:`str`
        A Discord timestamp.
    """
    dt = utcnow() + timedelta(seconds=seconds)
    return format_dt(dt, style)


def convert_to_seconds(string: str) -> int:
    """Convert a string to seconds. Supports multiple units and decimal separators.

    Parameters
    ----------
    string:
        The string to convert.

    Example
    -------
    >>> convert_to_seconds("1m 9s")
    69
    >>> convert_to_seconds("1.5m")
    90
    >>> convert_to_seconds("1,5 min")
    90
    >>> convert_to_seconds("1h 5m 10s")
    3910

    Returns
    -------
    :class:`int`
        The amount of seconds.
    """
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "t": "days", "w": "weeks"}

    pattern = re.compile(r"(?P<value>\d+([.,]\d+)?) *(?P<unit>[smhdtw]?)", flags=re.IGNORECASE)
    matches = pattern.finditer(string)

    found_units = {}
    for match in matches:
        unit = match.group("unit").lower()
        value = float(match.group("value").replace(",", "."))
        found_units[units.get(unit, "seconds")] = value

    return int(timedelta(**found_units).total_seconds())
