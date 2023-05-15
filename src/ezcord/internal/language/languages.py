import json
import os
from functools import cache
from pathlib import Path


@cache
def load_txt(language: str) -> dict:
    """Load default language files and check if the user provided custom language files."""

    lang = {}
    parent = Path(__file__).parent.absolute()
    for element in os.scandir(parent):
        if not element.is_file() or not element.name.endswith(f"{language}.json"):
            continue

        with open(os.path.join(parent, f"{language}.json"), encoding="utf-8") as file:
            lang = json.load(file)
            break

    # check if the user has a custom language file
    for root, directories, files in os.walk(os.getcwd()):
        for filename in files:
            if filename != f"ez_{language}.json":
                continue

            path = os.path.join(root, filename)
            with open(path, encoding="utf-8") as user_file:
                user_dic = json.load(user_file)
                for key, value in user_dic.items():
                    lang[key] = value

    return lang
