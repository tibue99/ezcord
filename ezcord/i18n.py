from __future__ import annotations

import inspect
import re
import traceback
from pathlib import Path
from typing import Literal

from .internal.dc import discord
from .logs import log

INTERACTION_SEND = discord.InteractionResponse.send_message
INTERACTION_EDIT = discord.InteractionResponse.edit_message
INTERACTION_EDIT_ORIGINAL = discord.Interaction.edit_original_response

WEBHOOK_SEND = discord.Webhook.send
WEBHOOK_EDIT = discord.WebhookMessage.edit


def extract_parameters(func, **kwargs):
    """Extract all kwargs that are not part of the function signature."""
    params = inspect.signature(func).parameters
    variables = {key: kwargs.pop(key) for key, value in kwargs.copy().items() if key not in params}
    return variables, kwargs


def ensure_interaction(interaction) -> discord.Interaction:
    """Extracts and returns the interaction from the given object."""

    if isinstance(interaction, discord.InteractionResponse):
        return interaction._parent
    if isinstance(interaction, discord.Interaction):
        return interaction
    return interaction


def _check_embed(locale: str, **kwargs):
    embed = kwargs.get("embed")
    if embed and isinstance(embed, str):
        new_embed = I18N.load_embed(embed, locale)
        kwargs["embed"] = new_embed
    elif embed:
        new_embed_dict = I18N.load_lang_keys(embed.to_dict(), locale)
        kwargs["embed"] = discord.Embed.from_dict(new_embed_dict)

    return kwargs


def _localize_send(send_func):
    async def wrapper(self: discord.InteractionResponse, content=None, **kwargs):
        if isinstance(self, discord.Webhook):
            locale = I18N.fallback_locale
        else:
            locale = I18N.get_locale(ensure_interaction(self))
        variables, kwargs = extract_parameters(send_func, **kwargs)

        # Check content
        content = I18N.get_text(content, locale)
        content = I18N.replace_variables(content, **variables)

        kwargs = _check_embed(locale, **kwargs)

        return await send_func(self, content, **kwargs)

    return wrapper


def _localize_edit(edit_func):
    async def wrapper(self: discord.InteractionResponse | discord.Interaction, **kwargs):
        locale = I18N.get_locale(ensure_interaction(self))
        variables, kwargs = extract_parameters(edit_func, **kwargs)

        # Check content (must be a kwarg)
        content = kwargs.get("content")
        if content:
            new_content = I18N.get_text(content, locale)
            new_content = I18N.replace_variables(new_content, **variables)
            kwargs["content"] = new_content

        return await edit_func(self, **kwargs)

    return wrapper


def t(interaction: discord.Interaction, key: str, **kwargs):
    """Get the localized string for the given key and inserts all variables."""
    locale = I18N.get_locale(interaction)

    content = I18N.get_text(key, locale)
    content = I18N.replace_variables(content, **kwargs)
    return content


class I18N:
    """A simple class to handle the localization of strings.

    A list of available languages is available here:
    https://discord.com/developers/docs/reference#locales

    Parameters
    ----------
    localizations:
        A dictionary containing the localizations for all strings.

        If an ``en`` key is found, the values will be used for both ``en-GB`` and ``en-US``.
    namespace:
        The structure to load the localization keys.
    process_strings:
        Whether to replace general variables when loading the language file. Defaults to ``True``.
    prefer_user_locale:
        Whether to prefer the user's locale over the guild's locale. Defaults to ``False``.
    debug:
        Whether to print debug messages. Defaults to ``True``.

        The log level in :meth:`ezcord.logs.set_log` must be set to ``DEBUG`` for this to work.
    """

    localizations: dict[str, dict]
    fallback_locale: str
    namespace: str
    prefer_user_locale: bool
    debug: bool

    _general_values: dict = {}  # general values for the current localization
    _current_general: dict = {}  # general values for the current group

    def __init__(
        self,
        localizations: dict[str, dict],
        *,
        fallback_locale: str = "en",
        namespace: str = "{file_name}.{command_name}.{key}",
        process_strings: bool = True,
        prefer_user_locale: bool = False,
        disable_translations: list[
            Literal[
                "send_message",
                "edit_message",
                "edit_original_response",
                "webhook_send",
                "webhook_edit_message",
            ]
        ]
        | None = None,
        debug: bool = True,
    ):
        if "en" in localizations:
            en = localizations.pop("en")
            localizations["en-GB"] = en
            localizations["en-US"] = en

        if process_strings:
            I18N.localizations = self.process_strings(localizations)
        else:
            I18N.localizations = localizations

        I18N.fallback_locale = fallback_locale
        I18N.namespace = namespace
        I18N.prefer_user_locale = prefer_user_locale
        I18N.debug = debug

        if not disable_translations:
            disable_translations = []

        if "send_message" not in disable_translations:
            setattr(discord.InteractionResponse, "send_message", _localize_send(INTERACTION_SEND))
        if "edit_message" not in disable_translations:
            setattr(discord.InteractionResponse, "edit_message", _localize_edit(INTERACTION_EDIT))
        if "edit_original_response" not in disable_translations:
            setattr(
                discord.Interaction,
                "edit_original_response",
                _localize_edit(INTERACTION_EDIT_ORIGINAL),
            )
        if "webhook_send" not in disable_translations:
            setattr(discord.Webhook, "send", _localize_send(WEBHOOK_SEND))
        if "webhook_edit_message" not in disable_translations:
            setattr(discord.WebhookMessage, "edit_message", _localize_edit(WEBHOOK_EDIT))

    @staticmethod
    def get_locale(interaction: discord.Interaction | discord.InteractionResponse):
        """Get the locale from the interaction. By default, this is the guild's locale."""
        interaction = ensure_interaction(interaction)

        if interaction.guild and not I18N.prefer_user_locale:
            locale = interaction.guild_locale
        else:
            locale = interaction.locale

        if locale not in I18N.localizations:
            return I18N.fallback_locale
        return locale

    @staticmethod
    def get_location():
        """Returns the name of the file and the method for the current interaction."""
        stack = traceback.extract_stack()

        file, method = None, None
        for i in list(reversed(stack))[2:]:
            if i.name not in [
                "wrapper",
                "respond",
                I18N.load_lang_keys.__name__,
                _check_embed.__name__,
            ]:
                file = i.filename
                method = i.name
                break

        return Path(file).stem, method

    @staticmethod
    def replace_variables(string: str, **kwargs):
        """Replace all variables in the string with the given kwargs.

        Example:
            replace_variables("Hello {name}", name="Timo")
            >>> "Hello Timo"
        """
        if not string:
            return string

        for key, value in kwargs.items():
            string = string.replace("{" + key + "}", str(value))

        return string

    @staticmethod
    def get_text(key: str, locale: str) -> str:
        """Looks for the specified key in different locations of the language file."""
        file_name, method_name = I18N.get_location()
        lookups = [
            (file_name, method_name, key),
            (file_name, "general", key),
            ("general", key),
        ]
        localizations = I18N.localizations[locale]

        for lookup in lookups:
            current_section = localizations.copy()
            for location in lookup:
                current_section = current_section.get(location, {})

            txt = current_section
            if isinstance(txt, str):
                return txt

        return key

    @staticmethod
    def load_embed(key: str, locale: str) -> discord.Embed:
        """Loads an embed from the language file."""

        file, cmd_name = I18N.get_location()
        try:
            embed_dict = I18N.localizations[locale][Path(file).stem][cmd_name]["embeds"][key]
            I18N.load_lang_keys(embed_dict, locale)

        except KeyError as e:
            if I18N.debug:
                log.debug(f"Key {e} not found when loading embed for key '{key}'.")
            return discord.Embed(description=key, color=discord.Color.blurple())

        return discord.Embed.from_dict(embed_dict)

    @staticmethod
    def load_lang_keys(content: dict | str, locale: str) -> dict | str:
        """Iterates through the content, loads the keys from the language file
        and replaces all variables with their values.
        """

        if isinstance(content, str):
            content = I18N.get_text(content, locale)
            return I18N.replace_variables(content)

        for key, value in content.items():
            if isinstance(value, str):
                value = I18N.get_text(value, locale)
                content[key] = I18N.replace_variables(value)
            elif isinstance(value, list):
                items = []
                for element in value:
                    items.append(I18N.load_lang_keys(element, locale))
                content[key] = items
            elif isinstance(value, dict):
                content[key] = I18N.load_lang_keys(value, locale)

        return content

    @staticmethod
    def _replace_general_variables(string: str) -> str:
        """Replaces global and local general variables with their values."""

        def replace_global(match: re.Match):
            match = match.group().replace("{.", "").replace("}", "")

            if match in I18N._current_general:
                return I18N._current_general[match]

            if match in I18N._general_values:
                return I18N._general_values[match]

            return match

        def replace_local(match: re.Match) -> str:
            match = match.group().replace("{general.", "").replace("}", "")
            if match in I18N._general_values:
                return I18N._general_values[match]

            return str(match)

        string = re.sub(r"{\..*}", replace_global, string)
        string = re.sub(r"{general.*}", replace_local, string)
        return string

    @staticmethod
    def _replace_dict(content: dict | str) -> dict | str:
        """Iterates through the content and replaces all general variables with their values.

        This is only needed once when loading the language file.
        """
        if isinstance(content, dict) and "general" in content:
            I18N._current_general = content["general"]

        if isinstance(content, str):
            return I18N._replace_general_variables(content)

        for key, value in content.items():
            if isinstance(value, str):
                content[key] = I18N._replace_general_variables(value)
            elif isinstance(value, dict):
                content[key] = I18N._replace_dict(value)

        return content

    @staticmethod
    def process_strings(localizations: dict) -> dict:
        """Process all strings and replace general variables when loading the language file.

        A general variable is defined in one of the "general" sections of the language files.
        """
        new_dict = {}
        for locale, values in localizations.items():
            if "general" in values:
                I18N._general_values = values["general"]

            new_dict[locale] = I18N._replace_dict(values)

        return new_dict
