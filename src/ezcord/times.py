from datetime import timezone, datetime

from .utils import tp


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


def convert_time(seconds: int, relative=True) -> str:
    """Convert seconds to a human-readable time.

    Parameters
    ----------
    seconds: :class:`int`
        The amount of seconds to convert.
    relative: :class:`bool`
        Whether to use relative time. Defaults to ``True``.

        .. hint::
            This is only needed for German translation and will
            not have any effect if the language is set to English.

    Returns
    -------
    :class:`str`
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
