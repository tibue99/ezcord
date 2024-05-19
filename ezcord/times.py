from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Literal

from .errors import ConvertTimeError, DurationError
from .internal import tp
from .internal.dc import discord

if TYPE_CHECKING:
    from .i18n import LOCALE_OBJECT


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


def convert_time(
    seconds: int | float, relative: bool = True, *, use_locale: LOCALE_OBJECT | None = None
) -> str:
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
    use_locale:
        The object to get the language from. Defaults to ``None``.
        If not provided, the language will be set to the default language.

    Returns
    -------
    :class:`str`
        A human-readable time.
    """
    if seconds < 60:
        return f"{round(seconds)} {tp('sec', round(seconds), use_locale=use_locale)}"
    minutes = seconds / 60
    if minutes < 60:
        return f"{round(minutes)} {tp('min', round(minutes), use_locale=use_locale)}"
    hours = minutes / 60
    if hours < 24:
        return f"{round(hours)} {tp('hour', round(hours), use_locale=use_locale)}"
    days = hours / 24
    return f"{round(days)} {tp('day', round(days), relative=relative, use_locale=use_locale)}"


def convert_dt(
    dt: datetime | timedelta,
    relative: bool = True,
    *,
    use_locale: LOCALE_OBJECT | None = None,
) -> str:
    """Convert :class:`datetime` or :class:`timedelta` to a human-readable time.

    This function calls :func:`convert_time`.

    Parameters
    ----------
    dt:
        The datetime or timedelta object to convert.
    relative:
        Whether to use relative time. Defaults to ``True``.
    use_locale:
        The interaction to get the language from. Defaults to ``None``.
        If not provided, the language will be set to the default language.

    Returns
    -------
    :class:`str`
        A human-readable time.
    """
    if isinstance(dt, timedelta):
        return convert_time(abs(dt.total_seconds()), relative, use_locale=use_locale)

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.astimezone()

        return convert_time(
            abs((dt - datetime.now(timezone.utc)).total_seconds()), relative, use_locale=use_locale
        )


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
    dt = discord.utils.utcnow() + timedelta(seconds=seconds)
    return discord.utils.format_dt(dt, style)


def convert_to_seconds(
    string: str, error: bool = False, default_unit: Literal["s", "m", "h", "d"] | None = "m"
) -> int:
    """Convert a string to seconds. Supports multiple units and decimal separators.

    Parameters
    ----------
    string:
        The string to convert.
    error:
        Whether to raise an error if the string could not be converted. If set to ``False``,
        the function will return ``0`` instead. Defaults to ``False``.
    default_unit:
        The default unit to use if no valid unit is specified. Defaults to ``m``.
        If at least one valid unit is found, all numbers without a valid unit are ignored.

    Returns
    -------
    :class:`int`
        The amount of seconds.

    Raises
    ------
    :exc:`ConvertTimeError`
         No valid number was found, or ``default_unit`` is ``None`` while no valid unit was found.
    :exc:`DurationError`
        The duration is too long.

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
    """
    units = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "t": "days",
        "w": "weeks",
        "mo": "months",
    }

    pattern = re.compile(r"(?P<value>\d+([.,]\d+)?) *(?P<unit>mo|[smhdtw]?)", flags=re.IGNORECASE)
    matches = pattern.finditer(string)

    no_unit = "0"
    found_units = {}
    for match in matches:
        unit_char = match.group("unit").lower()
        value = float(match.group("value").replace(",", "."))

        unit = units.get(unit_char, no_unit)
        found_units[unit] = value

    if no_unit in found_units:  # Number without valid unit found
        if len(found_units) <= 1:
            # No valid unit found -> Default unit is associated with the number
            if default_unit is not None:
                found_units[units[default_unit]] = found_units[no_unit]

        del found_units[no_unit]

    if error and not found_units:
        raise ConvertTimeError(f"Could not convert '{string}' to seconds.")

    if "months" in found_units:
        found_units.setdefault("days", 0)
        found_units["days"] = found_units["months"] * 30
        del found_units["months"]

    try:
        return int(timedelta(**found_units).total_seconds())
    except OverflowError:
        if error:
            raise DurationError(f"Duration '{string}' is too long.")
        return 0
