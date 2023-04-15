"""Some logging utilities that are used for bot logs."""

from __future__ import annotations

import logging
import os
import sys
from enum import Enum

from colorama import Fore

DEFAULT_LOG = "ezcord"
log = logging.getLogger(DEFAULT_LOG)


DEFAULT_LOG_COLORS: dict[int, str] = {
    logging.DEBUG: Fore.WHITE,
    logging.INFO: Fore.CYAN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.LIGHTRED_EX,
    logging.CRITICAL: Fore.RED,
}


class LogFormat(str, Enum):
    """Presets for logging formats that can be used in :func:`set_log`.

    ``{color_start}`` and ``{color_end}`` are used to add colors to parts of the log message.
    If they are not used, the whole log message will be colored.
    """

    default = "[%(asctime)s] %(levelname)s: %(message)s"
    color_level = "[{color_start}%(name)s{color_end}] %(message)s"
    color_name = "[{color_start}%(levelname)s{color_end}] %(message)s"

    def __str__(self):
        return self.value


def _format_colors(log_format: str, colors: dict[int, str] | str | None = None):
    """Overwrite the default colors for the given log levels in the given format."""

    final_colors = DEFAULT_LOG_COLORS.copy()
    if colors is None:
        colors = final_colors

    if isinstance(colors, str):
        for level in final_colors:
            final_colors[level] = colors
    else:
        for level in colors:
            final_colors[level] = colors[level]

    color_formats = {}
    if "{color_start}" in log_format and "{color_end}" in log_format:
        for level in final_colors:
            color_formats[level] = log_format.format(
                color_start=final_colors[level], color_end=Fore.RESET
            )
    else:
        for level in final_colors:
            color_formats[level] = final_colors[level] + log_format + Fore.RESET

    return color_formats


class ColorFormatter(logging.Formatter):
    """A logging formatter that adds colors to the output. This is used by :func:`set_log`.

    Parameters
    ----------
    file:
        Whether to log to a file.
    log_format:
        The log format.
    time_format:
        The time format.
    colors:
        Colors for the log levels.
    """

    def __init__(
        self,
        file: bool,
        log_format: str,
        time_format: str,
        colors: dict[int, str] | str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.file = file
        self.LOG_FORMAT = log_format
        self.TIME_FORMAT = time_format
        self.COLOR_FORMATS = _format_colors(log_format, colors)

    def format(self, record):
        """Check if the log is being sent to a file or not and format it accordingly."""
        if self.file:
            formatter = logging.Formatter(self.LOG_FORMAT, self.TIME_FORMAT)
        else:
            log_format = self.COLOR_FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_format, self.TIME_FORMAT)
        return formatter.format(record)


def set_log(
    name: str = DEFAULT_LOG,
    log_level: int = logging.INFO,
    file: bool = False,
    log_format: str | LogFormat = LogFormat.default,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    colors: dict[int, str] | str | None = None,
):
    """Creates a logger. If this logger already exists, it will return the existing logger.

    Parameters
    ----------
    name:
        The name of the logger.
    log_level:
        Whether to enable debug logs. Defaults to ``logging.INFO``.
    file:
        Whether to log to a file. Defaults to ``False``.
    log_format:
        The log format. Defaults to :attr:`LogFormat.default`.
    time_format:
        The time format. Defaults to ``%Y-%m-%d %H:%M:%S``.
    colors:
        A dictionary of log levels and their corresponding colors. If only one color is given,
        all log levels will be colored with that color.

        Example
        -------
        .. code-block:: python

            import logging
            from colorama import Fore
            import ezcord

            colors = {
                logging.DEBUG: Fore.GREEN,
                logging.INFO: Fore.CYAN,
            }

            ezcord.set_log(colors=colors)

    Returns
    -------
    :class:`logging.Logger`
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    handler: logging.FileHandler | logging.StreamHandler
    if file:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        filename = name.split(".")[-1]
        handler = logging.FileHandler(f"logs/{filename}.log", mode="w", encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(ColorFormatter(file, log_format, time_format, colors))
    logger.addHandler(handler)
    return logger
