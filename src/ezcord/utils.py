import os
import inspect
from configparser import ConfigParser

from .translation import *


def t(txt, *args):
    origin_file = os.path.basename(inspect.stack()[1].filename)[:-3]

    lang = get_lang()

    if lang == "de":
        return de[origin_file][txt].format(*args)
    else:
        return en[origin_file][txt].format(*args)


def get_lang():
    config = ConfigParser()
    config.read("config.ini")

    return config["DEFAULT"]["lang"]
