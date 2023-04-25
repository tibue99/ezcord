"""Some logging utilities that are used for bot logs."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import aiohttp
import discord
from colorama import Fore

from .enums import LogFormat
from .internal.colors import DEFAULT_COLOR, get_escape_code

DEFAULT_LOG = "ezcord"
log = logging.getLogger(DEFAULT_LOG)


DEFAULT_LOG_COLORS: dict[int, str] = {
    logging.DEBUG: Fore.GREEN,
    logging.INFO: Fore.CYAN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.LIGHTRED_EX,
    logging.CRITICAL: Fore.RED,
}


def custom_log(
    key: str, message: str, *, color: str | bool = DEFAULT_COLOR, level: int = logging.INFO
):
    """Log a message with a custom log level. This works only when using :attr:`ezcord.LogFormat.default`.

    Parameters
    ----------
    key:
        The name of the custom log level.
    message:
        The message to log.
    color:
        The color to use for the log level. Defaults to ``Fore.MAGENTA``.
    level:
        The log level. Defaults to ``logging.INFO``.
    """
    color = get_escape_code(color)
    logging.getLogger(DEFAULT_LOG).log(level, message, extra={"key": key, "color": color})


def _format_log_colors(log_format: str, file: bool, final_colors: dict[int, str]) -> dict[int, str]:
    """Checks if the is sent to a file and formats the colors accordingly."""
    color_formats = {}
    if "{color_start}" in log_format and "{color_end}" in log_format:
        for level in final_colors:
            if file:
                color_formats[level] = log_format.format(color_start="", color_end="")
            else:
                color_formats[level] = log_format.format(
                    color_start=final_colors[level], color_end=Fore.RESET
                )
    else:
        for level in final_colors:
            color_formats[level] = final_colors[level] + log_format + Fore.RESET

    return color_formats


def _format_colors(colors: dict[int, str] | str | None = None) -> dict[int, str]:
    """Overwrite the default colors for the given log levels in the given format."""

    final_colors = DEFAULT_LOG_COLORS.copy()
    if colors is None:
        colors = final_colors

    if isinstance(colors, str):
        colors = get_escape_code(colors)
        for level in final_colors:
            final_colors[level] = colors
    else:
        for level in colors:
            final_colors[level] = get_escape_code(colors[level])

    return final_colors


class _ColorFormatter(logging.Formatter):
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
        self.colors = colors
        self.LOG_FORMAT = log_format
        self.TIME_FORMAT = time_format

    def format(self, record: logging.LogRecord):
        """Adds colors to log messages and formats them accordingly.
        Can be used with :func:`set_log`.

        Parameters
        ----------
        record:
            The log record to format.
        """
        if "color" in record.__dict__:
            colors = record.__dict__["color"]
        else:
            colors = self.colors

        color_formats = _format_colors(colors)

        if record.levelno not in color_formats:
            if "color" in record.__dict__:
                # if a custom log level is used by .custom_log()
                color_formats[record.levelno] = colors
            else:
                # if no color is set for a custom log level used by .log()
                color_formats[record.levelno] = Fore.MAGENTA

        color_log_formats = _format_log_colors(self.LOG_FORMAT, self.file, color_formats)

        log_format = color_log_formats.get(record.levelno)
        if "key" in record.__dict__ and log_format:
            log_format = log_format.replace("%(levelname)s", record.__dict__["key"])

        formatter = logging.Formatter(log_format, self.TIME_FORMAT)
        return formatter.format(record)


class _DiscordHandler(logging.Handler):
    """A logging handler that sends logs to a Discord webhook."""

    def __init__(self, discord_log_level: int, webhook_url: str | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_url = webhook_url
        self.discord_log_level = discord_log_level

    def emit(self, record: logging.LogRecord):
        if "discord" in record.__dict__:
            record.message = record.__dict__["discord"]

        if record.levelno >= self.discord_log_level and self.webhook_url:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_send_discord_log(self.webhook_url, record))
            else:
                loop.run_until_complete(_send_discord_log(self.webhook_url, record))


async def _send_discord_log(webhook_url: str, record: logging.LogRecord):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        name = "EzCord" if record.name == DEFAULT_LOG else record.name
        try:
            await webhook.send(
                content=record.message,
                username=f"{name}: {record.levelname}",
            )
        except discord.HTTPException:
            log.error(
                "Error while sending log message to webhook. " "Please check if the URL is correct."
            )


def _discord_filter(record):
    if "webhook" in record.__dict__:
        return False
    return True


def set_log(
    name: str = DEFAULT_LOG,
    log_level: int = logging.DEBUG,
    file: bool = False,
    log_format: str | LogFormat = LogFormat.default,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    discord_log_level: int = logging.WARNING,
    webhook_url: str | None = None,
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
    discord_log_level:
        The log level for the discord.py logger. Defaults to ``logging.WARNING``.
    webhook_url:
        The discord webhook URL to send logs to. Defaults to ``None``.
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
                logging.DEBUG: "blue",
                logging.INFO: Fore.MAGENTA,
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

    handler.setFormatter(_ColorFormatter(file, log_format, time_format, colors))
    logger.addHandler(handler)

    discord_handler = _DiscordHandler(discord_log_level, webhook_url)
    discord_handler.addFilter(_discord_filter)
    logger.addHandler(discord_handler)
    return logger
