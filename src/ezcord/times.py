from datetime import timezone, datetime

from .utils import t

def set_utc(dt: datetime):
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


def convert_time(seconds: int) -> str:
    """Convert seconds to a human-readable time.

    Parameters
    ----------
    seconds: :class:`int`
        The amount of seconds to convert.

    Returns
    -------
    :class:`str`
    """
    if seconds < 60:
        return f"{round(seconds)} {t('sec')}"
    minutes = seconds / 60
    if minutes < 60:
        return f"{round(minutes)} {t('min')}"
    hours = minutes / 60
    if hours < 24:
        return f"{round(hours)} {t('hour')}"
    days = hours / 24
    return f"{round(days)} {t('day')}"
