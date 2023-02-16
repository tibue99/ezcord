import logging
import os
import sys

LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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

    handler.setFormatter(logging.Formatter(LOG_FORMAT, TIME_FORMAT))
    logger.addHandler(handler)
    return logger
