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

from .internal.colors import (  # isort: skip
    DEFAULT_COLOR,
    DEFAULT_LOG_COLORS,
    get_escape_code,
    replace_dc_format,
)

DEFAULT_LOG = "ezcord"
log = logging.getLogger(DEFAULT_LOG)


def custom_log(
    key: str, message: str, *, color: str | bool = DEFAULT_COLOR, level: int = logging.INFO
):
    """Log a message with a custom log level.

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
    if "{color}" in log_format and "{color_end}" in log_format:
        for level in final_colors:
            if file:
                color_formats[level] = log_format.format(color="", color_end="")
            else:
                color_formats[level] = log_format.format(
                    color=final_colors[level], color_end=Fore.RESET
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
        dc_codeblocks: bool,
        colors: dict[int, str] | str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.file = file
        self.colors = colors
        self.dc_codeblocks = dc_codeblocks
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
                color_formats[record.levelno] = DEFAULT_COLOR

        color_log_formats = _format_log_colors(self.LOG_FORMAT, self.file, color_formats)

        log_format = color_log_formats.get(record.levelno)
        if "key" in record.__dict__ and log_format:
            log_format = log_format.replace("%(levelname)s", record.__dict__["key"])

        current_level_color = color_formats.get(record.levelno)
        new_record = logging.makeLogRecord(record.__dict__)

        # color new lines
        if isinstance(log_format, str) and log_format.endswith("//"):
            log_format = log_format.replace("//", "")
            split = new_record.msg.split("\n", 1)
            if len(split) > 1:
                new_record.msg = split[0] + "\n**" + split[1] + "**"

        new_record.msg = replace_dc_format(new_record.msg, current_level_color)

        formatter = logging.Formatter(log_format, self.TIME_FORMAT)
        return formatter.format(new_record)


class _DiscordHandler(logging.Handler):
    """A logging handler that sends logs to a Discord webhook."""

    def __init__(
        self, webhook_url: str | None, dc_codeblocks: bool, dc_format: str, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.webhook_url = webhook_url
        self.dc_codeblocks = dc_codeblocks
        self.dc_format = dc_format

    def emit(self, record: logging.LogRecord):
        """Removes exception information and sets the log format."""
        record._exc_info_hidden, record.exc_info = record.exc_info, None
        record.exc_text = None

        if self.dc_codeblocks:
            msg = f"```ansi\n{self.format(record)}```"
        else:
            if "key" in record.__dict__:
                log_format = self.dc_format.replace("%(levelname)s", record.__dict__["key"])

                formatter = logging.Formatter(log_format)
                msg = formatter.format(record)
            else:
                msg = self.format(record)

        if self.webhook_url:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_send_discord_log(self.webhook_url, record, msg))
            else:
                loop.run_until_complete(_send_discord_log(self.webhook_url, record, msg))


async def _send_discord_log(webhook_url: str, record: logging.LogRecord, msg):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        name = "EzCord" if record.name == DEFAULT_LOG else record.name
        try:
            await webhook.send(
                content=msg,
                username=f"{name} Log",
            )
        except discord.HTTPException:
            log.error(
                "Error while sending log message to webhook. Please check if the URL is correct."
            )


def _discord_filter(record):
    """A filter that blocks logs that have already been sent to a Discord webhook."""
    if "webhook_sent" in record.__dict__:
        return not record.__dict__["webhook_sent"]
    return True


def set_log(
    name: str = DEFAULT_LOG,
    log_level: int = logging.DEBUG,
    *,
    file: bool = False,
    log_format: str | LogFormat = LogFormat.default,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    discord_log_level: int = logging.WARNING,
    webhook_url: str | None = None,
    dc_codeblocks: bool = True,
    colors: dict[int, str] | str | None = None,
):
    """Creates a logger. If this logger already exists, it will return the existing logger.

    Parameters
    ----------
    name:
        The name of the logger.
    log_level:
        The log level for default log messages ``logging.DEBUG``.
    file:
        Whether to log to a file. Defaults to ``False``.
    log_format:
        The log format. Defaults to :attr:`.LogFormat.default`.
    time_format:
        The time format. Defaults to ``%Y-%m-%d %H:%M:%S``.
    discord_log_level:
        The log level for discord log messages. Defaults to ``logging.WARNING``.

        .. note::
            For discord log messages, ``webhook_url`` is required.
    webhook_url:
        The discord webhook URL to send logs to. Defaults to ``None``.
    dc_codeblocks:
        Whether to use codeblocks for all Discord log messages. Defaults to ``True``.
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
    logger.setLevel(log_level)
    if logger.handlers:
        return logger

    handler: logging.FileHandler | logging.StreamHandler
    if file:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        filename = name.split(".")[-1]
        handler = logging.FileHandler(f"logs/{filename}.log", mode="w", encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    color_formatter = _ColorFormatter(file, log_format, time_format, dc_codeblocks, colors)

    handler.setFormatter(color_formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)

    dc_format = "**%(levelname)s:** %(message)s"
    discord_handler = _DiscordHandler(webhook_url, dc_codeblocks, dc_format)
    if dc_codeblocks:
        discord_handler.setFormatter(color_formatter)
    else:
        discord_handler.setFormatter(logging.Formatter(dc_format))
    discord_handler.addFilter(_discord_filter)
    discord_handler.setLevel(discord_log_level)
    logger.addHandler(discord_handler)

    return logger
