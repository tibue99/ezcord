"""Some logging utilities that are used for bot logs.

.. note::
    These utilities are not meant to be used directly, instead they should
    be used through the :class:`ezcord.bot.Bot` class.
"""

from colorama import Fore

import logging
import os
import sys


class ColorFormatter(logging.Formatter):
    """A logging formatter that adds colors to the output.

    Parameters
    ----------
    file: :class:`bool`
        Whether to log to a file.
    log_format: :class:`str`
        The log format.
    time_format: :class:`str`
        The time format.
    """
    def __init__(
            self,
            file: bool,
            log_format: str,
            time_format: str,
    ):
        super().__init__()

        color_formats = {
            logging.DEBUG: Fore.WHITE + log_format + Fore.RESET,
            logging.INFO: Fore.CYAN + log_format + Fore.RESET,
            logging.WARNING: Fore.YELLOW + log_format + Fore.RESET,
            logging.ERROR: Fore.LIGHTRED_EX + log_format + Fore.RESET,
            logging.CRITICAL: Fore.RED + log_format + Fore.RESET
        }

        self.file = file
        self.LOG_FORMAT = log_format
        self.TIME_FORMAT = time_format
        self.COLOR_FORMATS = color_formats

    def format(self, record):
        """Checks if the log is being sent to a file or not and formats it accordingly."""
        if self.file:
            formatter = logging.Formatter(self.LOG_FORMAT, self.TIME_FORMAT)
        else:
            log_format = self.COLOR_FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_format, self.TIME_FORMAT)
        return formatter.format(record)


def set_log(
        name: str,
        debug: bool = True,
        file: bool = False,
        log_format: str = "[%(asctime)s] %(levelname)s: %(message)s",
        time_format: str = "%Y-%m-%d %H:%M:%S",
):
    """Creates a logger.

    Parameters
    ----------
    name: :class:`str`
        The name of the logger.
    debug: :class:`bool`
        Whether to enable debug logs. Defaults to ``True``.
    file: :class:`bool`
        Whether to log to a file. Defaults to ``False``.
    log_format: :class:`str`
        The log format. Defaults to ``[%(asctime)s] %(levelname)s: %(message)s``.
    time_format: :class:`str`
        The time format. Defaults to ``%Y-%m-%d %H:%M:%S``.
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')

    logger = logging.getLogger(name)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    if file:
        filename = name.split(".")[-1]
        handler = logging.FileHandler(f"logs/{filename}.log", mode="w", encoding='utf-8')
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(ColorFormatter(file, log_format, time_format))
    logger.addHandler(handler)
    return logger
