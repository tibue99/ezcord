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
    relative: :class:`bool`
        Whether to use relative time. Defaults to ``True``.

        .. hint::
            This is only needed for German translation and will
            not have any effect if the language is set to English.

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
    relative: :class:`bool`
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


def convert_to_seconds(s: str) -> int:
    """Convert a string to seconds.

    Parameters
    ----------
    s:
        The string to convert.

    Returns
    -------
    :class:`int`
        The amount of seconds.
    """
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
    return int(
        timedelta(
            **{
                units.get(m.group("unit").lower(), "seconds"): float(m.group("val"))
                for m in re.finditer(r"(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)", s, flags=re.I)
            }
        ).total_seconds()
    )
