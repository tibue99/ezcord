from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path

from ...internal import discord
from ...logs import log
from ..config import EzConfig


@cache
def load_lang(language: str) -> dict[str, dict[str, str]]:
    """Loads the given language file and checks if the user provided a custom language file."""

    if language == "auto":
        language = EzConfig.default_lang

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

            log.debug(f"Custom language file loaded: **{filename}**")

            path = os.path.join(root, filename)
            with open(path, encoding="utf-8") as user_file:
                user_dic = json.load(user_file)
                for category, values in user_dic.items():
                    for value in values:
                        if category not in lang:
                            lang[category] = {}
                        lang[category][value] = values[value]

    if EzConfig.lang != "auto" and lang == {}:
        log.warn(f"Language file for language '{language}' not found. Falling back to 'en'.")

    return lang


def localize_command(
    command: discord.ApplicationCommand | discord.SlashCommandGroup,
    locale: str,
    localizations: dict,
    default_locale: str,
):
    """Localize a slash command or a slash command group.

    This code is inspired by https://github.com/Dorukyum/pycord-i18n,
    which is licensed under the MIT License.
    """

    if isinstance(command, discord.SlashCommandGroup):
        for cmd in command.walk_commands():
            localize_command(cmd, locale, localizations.get(cmd.name, {}), default_locale)

    if name := localizations.get("name"):
        if locale == default_locale:
            command.name = name

        if command.name_localizations is discord.MISSING:
            command.name_localizations = {locale: name}
        else:
            command.name_localizations[locale] = name

    if not isinstance(command, discord.SlashCommand):
        return

    if description := localizations.get("description"):
        if locale == default_locale:
            command.description = description

        if command.description_localizations is discord.MISSING:
            command.description_localizations = {locale: description}
        else:
            command.description_localizations[locale] = description

    if options := localizations.get("options"):
        for option_name, localization in options.items():
            if option := discord.utils.get(command.options, name=option_name):
                if option_name := localization.get("name"):
                    if locale == default_locale:
                        option.name = option_name

                    if option.name_localizations is discord.MISSING:
                        option.name_localizations = {locale: option_name}
                    else:
                        option.name_localizations[locale] = option_name

                if option_desc := localization.get("description"):
                    if locale == default_locale:
                        option.description = option_desc

                    if option.description_localizations is discord.MISSING:
                        option.description_localizations = {locale: option_desc}
                    else:
                        option.description_localizations[locale] = option_desc

                if option_choices := localization.get("choices"):
                    for choice in option.choices:
                        if isinstance(choice, str):
                            choice = discord.OptionChoice(name=choice)

                        name = option_choices.get(choice.name)
                        if name:
                            if locale == default_locale:
                                choice.name = name

                            if choice.name_localizations is discord.MISSING:
                                choice.name_localizations = {locale: name}
                            else:
                                choice.name_localizations[locale] = name


def localize_cog(
    cog_name: str,
    cog,
    locale: str,
    localizations: dict,
):
    """Localize a cog. This is only used for the help command."""

    if localized_cog := localizations.get(cog_name):
        if localized_name := localized_cog.get("name"):
            if not hasattr(cog, "name_localizations"):
                cog.name_localizations = {locale: localized_name}
            else:
                cog.name_localizations[locale] = localized_name

        if localized_desc := localized_cog.get("description"):
            if not hasattr(cog, "description_localizations"):
                cog.description_localizations = {locale: localized_desc}
            else:
                cog.description_localizations[locale] = localized_desc
