from colorama import Fore

import logging
import os
import sys


class ColorFormatter(logging.Formatter):
    def __init__(self, file: bool):
        super().__init__()
        self.file = file

    LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FORMATS = {
        logging.DEBUG: Fore.WHITE + LOG_FORMAT + Fore.RESET,
        logging.INFO: Fore.CYAN + LOG_FORMAT + Fore.RESET,
        logging.WARNING: Fore.YELLOW + LOG_FORMAT + Fore.RESET,
        logging.ERROR: Fore.LIGHTRED_EX + LOG_FORMAT + Fore.RESET,
        logging.CRITICAL: Fore.RED + LOG_FORMAT + Fore.RESET
    }

    def format(self, record):
        if self.file:
            formatter = logging.Formatter(self.LOG_FORMAT, self.TIME_FORMAT)
        else:
            log_format = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_format, self.TIME_FORMAT)
        return formatter.format(record)


def set_logs(name, debug=True, file=False):
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

    handler.setFormatter(ColorFormatter(file))
    logger.addHandler(handler)
    return logger
