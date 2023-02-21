import os
import inspect
from configparser import ConfigParser
from pathlib import Path

from .translation import *


def t(txt, *args):
    origin_file = os.path.basename(inspect.stack()[1].filename)[:-3]

    lang = get_lang()

    if lang == "de":
        return de[origin_file][txt].format(*args)
    else:
        return en[origin_file][txt].format(*args)


def get_lang():
    parent = Path(__file__).parent.absolute()
    config = ConfigParser()
    config.read(os.path.join(parent, "config.ini"))

    return config["DEFAULT"]["lang"]


def set_lang(lang):
    parent = Path(__file__).parent.absolute()
    config = ConfigParser()
    config["DEFAULT"] = {"lang": lang}

    with open(os.path.join(parent, "config.ini"), "w") as f:
        config.write(f)
