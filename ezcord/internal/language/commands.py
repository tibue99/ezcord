"""This code is inspired by https://github.com/Dorukyum/pycord-i18n,
which is licensed under the MIT License.
"""

from __future__ import annotations

from ...internal import discord


def localize_command(
    command: discord.ApplicationCommand | discord.SlashCommandGroup,
    locale: str,
    localizations: dict,
):
    """Localize a slash command or a slash command group."""

    if isinstance(command, discord.SlashCommandGroup):
        for cmd in command.walk_commands():
            localize_command(cmd, locale, localizations.get(cmd.name, {}))

    if name := localizations.get("name"):
        if command.name_localizations is discord.MISSING:
            command.name_localizations = {locale: name}
        else:
            command.name_localizations[locale] = name

    if isinstance(command, discord.SlashCommand):
        if description := localizations.get("description"):
            if command.description_localizations is discord.MISSING:
                command.description_localizations = {locale: description}
            else:
                command.description_localizations[locale] = description

        if options := localizations.get("options"):
            for option_name, localization in options.items():
                if option := discord.utils.get(command.options, name=option_name):
                    if option_name := localization.get("name"):
                        if option.name_localizations is discord.MISSING:
                            option.name_localizations = {locale: option_name}
                        else:
                            option.name_localizations[locale] = option_name

                    if option_desc := localization.get("description"):
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
                                if choice.name_localizations is discord.MISSING:
                                    choice.name_localizations = {locale: name}
                                else:
                                    choice.name_localizations[locale] = name
