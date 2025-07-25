from __future__ import annotations

import inspect
import random
import re
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Union

from .internal.dc import PYCORD, discord
from .logs import log

MESSAGE_SEND = discord.abc.Messageable.send
MESSAGE_REPLY = discord.Message.reply
MESSAGE_EDIT = discord.Message.edit

INTERACTION_SEND = discord.InteractionResponse.send_message
INTERACTION_EDIT = discord.InteractionResponse.edit_message
INTERACTION_MODAL = discord.InteractionResponse.send_modal

WEBHOOK_SEND = discord.Webhook.send
WEBHOOK_EDIT_MESSAGE = discord.Webhook.edit_message
WEBHOOK_EDIT = discord.WebhookMessage.edit

LOCALE = Union[str]

if PYCORD:
    INTERACTION_EDIT_ORIGINAL = discord.Interaction.edit_original_response
    if hasattr(discord.Interaction, "respond"):
        # older py-cord versions might not have this method
        INTERACTION_RESPOND = discord.Interaction.respond
    else:
        INTERACTION_RESPOND = None
else:
    INTERACTION_RESPOND = None
    if hasattr(discord.Interaction, "edit_original_message"):
        INTERACTION_EDIT_ORIGINAL = discord.Interaction.edit_original_message
    else:
        INTERACTION_EDIT_ORIGINAL = None


if TYPE_CHECKING:
    import discord  # type: ignore

    LOCALE = Union[  # type: ignore
        discord.Interaction,
        discord.ApplicationContext,
        discord.InteractionResponse,
        discord.Webhook,
        discord.Guild,
        discord.Member,
        str,
    ]

__all__ = ("t", "TEmbed", "I18N", "LOCALE")


def t(obj: LOCALE | str, key: str, count: int | None = None, **variables):
    """Get the localized string for the given key and insert all variables.

    Parameters
    ----------
    obj:
        The object to get the locale from.
    key:
        The key of the string in the language file.
    count:
        The count for pluralization. Defaults to ``None``.
    """
    locale = I18N.get_locale(obj)
    return I18N.load_text(key, locale, count, **variables)


class TEmbed(discord.Embed):
    """A subclass of :class:`discord.Embed` for localized embeds.

    Parameters
    ----------
    key:
        The key of the embed in the language file.
    kwargs:
        Parameters from :class:`discord.Embed` or custom variables.
    """

    def __init__(self, key: str = "embed", **kwargs):
        variables, kwargs = _extract_parameters(discord.Embed.__init__, **kwargs)
        super().__init__(**kwargs)
        self.key = key
        self.variables = variables

        _, method, class_ = I18N.get_location()
        self.method_name = method
        self.class_name = class_


def _extract_parameters(func, **kwargs):
    """Extract all kwargs that are not part of the function signature and returns them as
    a dictionary of variables.
    """
    params = inspect.signature(func).parameters
    variables = {key: kwargs.pop(key) for key, value in kwargs.copy().items() if key not in params}
    return variables, kwargs


def _check_embed(locale: str, count: int | None, variables: dict, **kwargs):
    """Check if the kwargs contain an embed. Returns the updated kwargs.

    - Embed is a TEmbed: Load the embed from the language file.
    - Embed is a default Embed: Load all keys inside the embed from the language file
    """

    add_locations: tuple = ()
    embed = kwargs.get("embed")
    if isinstance(embed, TEmbed):
        variables = {**variables, **embed.variables}
        add_locations = (embed.method_name, embed.class_name)
        embed = I18N.load_embed(embed, locale)

    if embed:
        if "count" in variables:
            count = variables["count"]
        new_embed_dict = I18N.load_lang_keys(
            embed.to_dict(), locale, count, add_locations, **variables
        )
        kwargs["embed"] = discord.Embed.from_dict(new_embed_dict)

    return kwargs


def _check_embeds(locale: str, count: int | None, variables: dict, **kwargs):
    """Check if the kwargs contain an embed list. Returns the updated kwargs."""

    add_locations: tuple = ()
    embeds = kwargs.get("embeds")
    if not embeds:
        return kwargs

    new_embeds = []
    for embed in embeds:
        if isinstance(embed, TEmbed):
            variables = {**variables, **embed.variables}
            add_locations = (embed.method_name, embed.class_name)
            embed = I18N.load_embed(embed, locale)

        if "count" in variables:
            count = variables["count"]
        new_embed_dict = I18N.load_lang_keys(
            embed.to_dict(), locale, count, add_locations, **variables
        )
        new_embeds.append(discord.Embed.from_dict(new_embed_dict))

    kwargs["embeds"] = new_embeds
    return kwargs


def _check_components(component, locale: str, count: int | None, class_name: str, **variables):
    """Recursively walks through components and loads language file keys."""

    if isinstance(component, discord.ui.Container):
        for item in component.items:
            _check_components(item, locale, count, class_name, **variables)

    if isinstance(component, discord.ui.Section):
        for item in component.items:
            _check_components(item, locale, count, class_name, **variables)

        _check_components(component.accessory, locale, count, class_name, **variables)

    # TextDisplay
    if hasattr(component, "content"):
        component.content = I18N.load_text(
            component.content, locale, count, class_name, **variables
        )

    if isinstance(component, discord.ui.Button) and hasattr(component, "label"):
        component.label = I18N.load_text(component.label, locale, count, class_name, **variables)

    if hasattr(component, "placeholder"):
        component.placeholder = I18N.load_text(
            component.placeholder, locale, count, class_name, **variables
        )

    if hasattr(component, "options"):
        for option in component.options:
            option.label = I18N.load_text(option.label, locale, count, class_name, **variables)
            option.description = I18N.load_text(
                option.description, locale, count, class_name, **variables
            )


def _check_view(locale: str, count: int | None, variables: dict, **kwargs):
    """Load all keys inside the view from the language file."""

    if "count" in variables:
        count = variables["count"]

    view = kwargs.get("view")
    if view:
        class_name = view.__class__.__name__
        for child in view.children:
            if type(child) not in [discord.ui.Select, discord.ui.Button]:
                # if a child element of the view has its own subclass, search for this class name
                # in the language file instead of the view name
                class_name = child.__class__.__name__

            _check_components(child, locale, count, class_name, **variables)

    return kwargs


def _localize_send(send_func):
    async def wrapper(
        self: (
            discord.InteractionResponse
            | discord.Webhook
            | discord.abc.Messageable
            | discord.Interaction
        ),
        content=None,
        *,
        count: int | None = None,
        use_locale: LOCALE | None = None,
        **kwargs,
    ):
        """Wrapper to localize the content and the embed of a message.

        Parameters
        ----------
        self:
            The object to send the message from.
        content:
            The content of the message.
        count:
            The count for pluralization. Defaults to ``None``.
        use_locale:
            Use a specific object to extract the locale from. This is useful for DMs
            or followup messages. Defaults to ``None``.
        """

        if isinstance(self, discord.Interaction):
            # This is used for cases where followup.send is executed inside of interaction.respond,
            # because the locale can't be extracted from application webhooks
            return await send_func(self, content, count=count, use_locale=self, **kwargs)

        locale = I18N.get_locale(use_locale or self)
        variables, kwargs = _extract_parameters(send_func, **kwargs)

        # Check content
        content = I18N.load_text(content, locale, **variables)

        kwargs = _check_embed(locale, count, variables, **kwargs)
        kwargs = _check_embeds(locale, count, variables, **kwargs)
        kwargs = _check_view(locale, count, variables, **kwargs)

        return await send_func(self, content, **kwargs)

    return wrapper


def _localize_edit(edit_func):
    async def wrapper(
        self: discord.InteractionResponse | discord.Interaction | discord.Message | discord.Webhook,
        message_id: int | None = None,
        *,
        count: int | None = None,
        use_locale: LOCALE | None = None,
        **kwargs,
    ):
        """The message_id is only needed for followup.edit_message, because it's a positional
        argument in the original function.

        The parameter "use_locale" is only needed for followup.edit_message,
        because the locale can't be extracted automatically.
        """
        locale = I18N.get_locale(use_locale or self)
        variables, kwargs = _extract_parameters(edit_func, **kwargs)

        # Check content (must be a kwarg)
        content = kwargs.get("content")
        if content:
            new_content = I18N.load_text(content, locale, count, **variables)
            kwargs["content"] = new_content

        kwargs = _check_embed(locale, count, variables, **kwargs)
        kwargs = _check_embeds(locale, count, variables, **kwargs)
        kwargs = _check_view(locale, count, variables, **kwargs)

        if isinstance(self, discord.Webhook):
            return await edit_func(self, message_id, **kwargs)

        return await edit_func(self, **kwargs)

    return wrapper


async def _localize_modal(
    self: discord.InteractionResponse,
    modal: discord.ui.Modal,
    *,
    count: int | None = None,
    **kwargs,
):
    locale = I18N.get_locale(self)
    variables, kwargs = _extract_parameters(INTERACTION_MODAL, **kwargs)
    modal_name = modal.__class__.__name__

    modal.title = I18N.load_text(modal.title, locale, count, modal_name, **variables)

    for child in modal.children:
        child.label = I18N.load_text(child.label, locale, count, modal_name, **variables)

        if hasattr(child, "placeholder"):
            child.placeholder = I18N.load_text(
                child.placeholder, locale, count, modal_name, **variables
            )
        if hasattr(child, "value"):
            child.value = I18N.load_text(child.value, locale, count, modal_name, **variables)

    return await INTERACTION_MODAL(self, modal)


class I18N:
    """A simple class to handle the localization of strings.

    A list of available languages is available here:
    https://discord.com/developers/docs/reference#locales

    .. note::
        Methods in this class are called automatically and do not need to be
        called manually in most cases.

    Parameters
    ----------
    localizations:
        A dictionary containing the localizations for all strings.

        If an ``en`` key is found, the values will be used for both ``en-GB`` and ``en-US``.
    fallback_locale:
        The locale to use if the user's locale is not found in the localizations.
        Defaults to ``en-US``.
    process_strings:
        Whether to replace general variables when loading the language file. Defaults to ``True``.
    prefer_user_locale:
        Whether to prefer the user's locale over the guild's locale. Defaults to ``False``.
    localize_numbers:
        This sets the thousands separator to a period or comma, depending on the current locale.
        Defaults to ``True``.
    ignore_discord_ids:
        Whether to not localize numbers that could be a Discord ID. Default to  ``True``.
        This only has an effect if ``localize_numbers`` is set to ``True``.
    do_not_localize:
        If a key starts with this string, it will not be localized. Defaults to ``".."``.
    exclude_methods:
        Method names to exclude from the search of keys in the language file.
    disable_translations:
        A list of translations to disable. Defaults to ``None``.

        The log level in :meth:`ezcord.logs.set_log` must be set to ``DEBUG`` for this to work.
    debug:
        Whether to send debug messages and warnings. Defaults to ``True``.
    language_settings:
        A function to set custom language settings. The function must return a dictionary
        with user/guild IDs as keys and the locale as values. Defaults to ``None``.
    variables:
        Additional variables to replace in the language file. This is useful for
        values that are the same in all languages.
    """

    localizations: dict[str, dict]
    fallback_locale: str
    prefer_user_locale: bool = False
    localize_numbers: bool
    ignore_discord_ids: bool
    do_not_localize: str = ".."
    exclude_methods: list[str] | None

    _general_values: dict = {}  # general values for the current localization
    _current_general: dict = {}  # general values for the current group

    cmd_localizations: dict[str, dict] = {}  # set through bot.localize_commands
    initialized: bool = False

    _custom_language_settings: Callable

    def __init__(
        self,
        localizations: dict[str, dict],
        *,
        fallback_locale: str = "en-US",
        process_strings: bool = True,
        prefer_user_locale: bool = False,
        localize_numbers: bool = True,
        ignore_discord_ids: bool = True,
        do_not_localize: str = "..",
        exclude_methods: list[str] | None = None,
        disable_translations: (
            list[
                Literal[
                    "send",
                    "edit",
                    "reply",
                    "send_message",
                    "send_modal",
                    "edit_message",
                    "edit_original_response",
                    "webhook_send",
                    "webhook_edit_message",
                ]
            ]
            | None
        ) = None,
        debug: bool = True,
        language_settings=None,
        **variables,
    ):
        I18N.initialized = True
        if "en" in localizations:
            en = localizations.pop("en")
            localizations["en-GB"] = en
            localizations["en-US"] = en

        if fallback_locale == "en":
            fallback_locale = "en-US"

        if process_strings:
            I18N.localizations = self._process_strings(localizations, **variables)
        else:
            I18N.localizations = localizations

        I18N.fallback_locale = fallback_locale
        I18N.prefer_user_locale = prefer_user_locale
        I18N.localize_numbers = localize_numbers
        I18N.ignore_discord_ids = ignore_discord_ids
        if not exclude_methods:
            exclude_methods = []
        I18N.exclude_methods = exclude_methods
        I18N.do_not_localize = do_not_localize
        I18N._custom_language_settings = language_settings

        if not disable_translations:
            disable_translations = []

        if debug:
            I18N._check_localizations()

        if "send" not in disable_translations:
            setattr(discord.abc.Messageable, "send", _localize_send(MESSAGE_SEND))
        if "edit" not in disable_translations:
            setattr(discord.Message, "edit", _localize_edit(MESSAGE_EDIT))
        if "reply" not in disable_translations:
            setattr(discord.Message, "reply", _localize_send(MESSAGE_REPLY))

        if "send_message" not in disable_translations:
            setattr(discord.InteractionResponse, "send_message", _localize_send(INTERACTION_SEND))
        if "send_modal" not in disable_translations:
            setattr(discord.InteractionResponse, "send_modal", _localize_modal)
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
            setattr(discord.Interaction, "respond", _localize_send(INTERACTION_RESPOND))
        if "webhook_edit_message" not in disable_translations:
            setattr(discord.Webhook, "edit_message", _localize_edit(WEBHOOK_EDIT_MESSAGE))
        if "webhook_edit_message" not in disable_translations:
            setattr(discord.WebhookMessage, "edit_message", _localize_edit(WEBHOOK_EDIT))

    @staticmethod
    def get_locale(obj: LOCALE) -> str:
        """Get the locale from the given object. By default, this is the guild's locale.

        This method can be called even if the I18N class has not been initialized.

        Parameters
        ----------
        obj:
            The object to get the locale from.
        """

        if isinstance(obj, str):
            if hasattr(I18N, "localizations") and obj not in I18N.localizations:
                return I18N.fallback_locale
            return obj

        guild_id, user_id = None, None

        # determine interaction
        interaction, locale = None, None
        if isinstance(obj, discord.Interaction):
            interaction = obj
        elif isinstance(obj, discord.InteractionResponse):
            interaction = obj._parent
        elif isinstance(obj, discord.ApplicationContext):
            interaction = obj.interaction

        # determine locale
        elif isinstance(obj, discord.Webhook) and obj.guild:
            locale = obj.guild.preferred_locale
            guild_id = obj.guild.id
        elif isinstance(obj, discord.Member):
            locale = obj.guild.preferred_locale
            guild_id = obj.guild.id
            user_id = obj.id
        elif isinstance(obj, discord.Guild):
            locale = obj.preferred_locale
            guild_id = obj.id

        elif (
            isinstance(obj, discord.abc.Messageable | discord.Message)
            and hasattr(obj, "guild")
            and obj.guild
        ):
            locale = obj.guild.preferred_locale
            guild_id = obj.guild.id

        elif isinstance(obj, discord.User):
            # It's not possible to determine the user locale without an interaction
            locale = I18N.fallback_locale
            user_id = obj.id

        if interaction:
            if interaction.guild and not I18N.prefer_user_locale:
                locale = interaction.guild_locale
                guild_id = interaction.guild.id
            else:
                locale = interaction.locale
                user_id = interaction.user.id

        # check custom language settings
        if hasattr(I18N, "_custom_language_settings") and I18N._custom_language_settings:
            if guild_id:
                custom_locale = I18N._custom_language_settings(guild_id)
                locale = custom_locale or locale
            if user_id:
                custom_locale = I18N._custom_language_settings(user_id)
                locale = custom_locale or locale

        # check if the locale is available. if not, use the fallback locale
        if hasattr(I18N, "localizations"):
            if locale not in I18N.localizations:
                return I18N.fallback_locale
            return locale

        return locale  # I18N class is not in use

    @staticmethod
    def get_clean_locale(obj: LOCALE) -> str:
        """Get the clean locale from the given object. This is the locale without the region,
        e.g. ``en`` instead of ``en-US``.

        Parameters
        ----------
        obj:
            The object to get the locale from.
        """
        locale = I18N.get_locale(obj)
        return locale.split("-")[0]

    @staticmethod
    def get_location():
        """Returns the name of the file, method and class for the current interaction.

        This can only get the class if a method was executed from inside the class.
        """

        inspect_stack = inspect.stack()

        # Ignore the following internal sources to determine the origin method
        # "sub" is used for regex substitution when searching for keys within other keys.
        methods = ["respond", "sub"] + I18N.exclude_methods
        files = ["i18n", "emb", "interactions"]

        file, method, class_ = None, None, None
        for i in inspect_stack[2:]:
            if i.function not in methods and Path(i.filename).stem not in files:
                try:
                    class_ = i.frame.f_locals["self"].__class__.__name__
                except KeyError:
                    pass  # No class found
                file = i.filename
                method = i.function
                break

        if file:
            file = Path(file).stem

        return file, method, class_

    @staticmethod
    def _replace_variables(string: str, locale: str, **variables):
        """Replace all given variables in the string. Supports localized numbers.

        Example
        -------
        >>> I18N._replace_variables("Hello {name}", name="Timo")
        "Hello Timo"
        """
        if not string:
            return string

        for key, value in variables.items():
            if I18N.localize_numbers and isinstance(value, int):
                if not (I18N.ignore_discord_ids and len(str(value)) >= 17):
                    value = f"{value:,}"
                    if locale == "de":
                        value = value.replace(",", ".")
            string = string.replace("{" + key + "}", str(value))

        return string

    @staticmethod
    def _get_text(
        key: str, locale: str, count: int | None, called_class: str | None, add_locations: tuple
    ) -> str:
        """Looks for the specified key in different locations of the language file."""

        if key.startswith(I18N.do_not_localize):
            return key.replace(I18N.do_not_localize, "", 1)

        file_name, method_name, class_name = I18N.get_location()

        lookups: list[list | tuple]
        if "." in key:
            lookups = [key.split("."), [file_name] + key.split(".")]
        else:
            lookups = [
                (file_name, method_name, key),
                (file_name, called_class, key),
                (file_name, class_name, key),
                (file_name, "general", key),
                ("general", key),
                (file_name, key),
            ]
            for location in add_locations:
                lookups.append((file_name, location, key))

        localizations = I18N.localizations[locale]

        for lookup in lookups:
            current_section = localizations.copy()
            for location in lookup:
                try:
                    current_section = current_section.get(location, {})
                except AttributeError:
                    return key

            txt = current_section
            if isinstance(txt, str):
                return txt
            elif isinstance(txt, int):
                return str(txt)
            elif isinstance(txt, list):
                return random.choice(txt)
            elif count is not None and isinstance(txt, dict):
                # Load pluralization if available
                if count == 0 and "zero" in txt:
                    return txt["zero"]
                elif count == 1 and "one" in txt:
                    return txt["one"]
                elif count > 1 and "many" in txt:
                    return txt["many"]
                elif str(count) in txt:
                    return txt[str(count)]

        return key

    @staticmethod
    def load_text(
        key: str,
        locale: str,
        count: int | None = None,
        called_class: str | None = None,
        add_locations: tuple = (),
        **variables,
    ):
        """A helper methods that calls :meth:`get_text` to load the specified key
        and :meth:`replace_variables` to replace the variables.

        A class name can be given if the kwargs contain a view or modal.
        This name will be used to load strings from the init method or from decorators, as the
        class can only be fetched automatically if a method was executed from inside the class.

        Additional locations can be added to the lookup by passing a tuple of strings.
        This is used to load embed keys from the location of the embed creation,
        instead of the location of the embed usage.
        """

        if key is None:
            return None

        string = I18N._get_text(key, locale, count, called_class, add_locations)

        if count:
            variables = {**variables, "count": count}
        string = I18N._replace_variables(string, locale, **variables)

        def replace_keys(m: re.Match):
            k = m.group(1)
            check_key = I18N._get_text(k, locale, count, called_class, add_locations)
            return check_key if check_key != k else m.group()

        # check if key contains other keys
        if "{" in string and "}" in string:
            string = re.sub(r"{(.*?)}", replace_keys, string)

        return I18N._replace_variables(string, locale, **variables)

    @staticmethod
    def load_embed(embed: TEmbed, locale: str) -> discord.Embed:
        """Loads an embed from the language file."""

        file_name, method_name, class_name = I18N.get_location()

        # search not only the location of the embed usage,
        # but also the location of the embed creation
        original_method, original_class = embed.method_name, embed.class_name

        lookups: list[list | tuple]
        if "." in embed.key:
            lookups = [embed.key.split("."), [file_name] + embed.key.split(".")]
        else:
            lookups = [
                (file_name, method_name, embed.key),
                (file_name, original_method, embed.key),
                (file_name, original_class, embed.key),
                (file_name, class_name, embed.key),
                (file_name, embed.key),
            ]

        localizations = I18N.localizations[locale]

        for lookup in lookups:
            current_section = localizations.copy()
            for location in lookup:
                current_section = current_section.get(location, {})

            if current_section:
                t_embed_dict = embed.to_dict()
                for key, value in current_section.items():
                    t_embed_dict[key] = value

                return discord.Embed.from_dict(t_embed_dict)

        return discord.Embed(description=embed.key, color=discord.Color.blurple())

    @staticmethod
    def load_lang_keys(
        content: dict | str,
        locale: str,
        count: int | None = None,
        add_locations: tuple = (),
        **variables,
    ) -> dict | str:
        """Iterates through the content, loads the keys from the language file
        and replaces all variables with their values.

        Does not modify the original content.
        """

        if isinstance(content, str):
            return I18N.load_text(content, locale, count, add_locations=add_locations, **variables)

        content = deepcopy(content)

        for key, value in content.items():
            if isinstance(value, str):
                if key in ["color", "colour", "type", "url", "timestamp", "image", "thumbnail"]:
                    continue

                content[key] = I18N.load_text(
                    value, locale, count, add_locations=add_locations, **variables
                )
            elif isinstance(value, list):
                items = []
                for element in value:
                    items.append(
                        I18N.load_lang_keys(element, locale, count, add_locations, **variables)
                    )
                content[key] = items
            elif isinstance(value, dict):
                content[key] = I18N.load_lang_keys(value, locale, count, add_locations, **variables)

        return content

    @staticmethod
    def _replace_general_variables(string: str) -> str:
        """Replaces global and local general variables with their values."""

        def replace_local(match: re.Match):
            match = match.group().replace("{.", "").replace("}", "")
            if match in I18N._current_general:
                return I18N._current_general[match]

            if match in I18N._general_values:
                return I18N._general_values[match]

            return match

        def replace_global(possible_match: re.Match) -> str:
            match = possible_match.group()
            clean_match = match.replace("{", "").replace("}", "")
            if clean_match in I18N._general_values:
                if type(I18N._general_values[clean_match]) is str:
                    return I18N._general_values[clean_match]

            return str(match)

        string = re.sub(r"{\..*?}", replace_local, string)
        string = re.sub(r"{.*?}", replace_global, string)
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
            if isinstance(value, list):
                items = []
                for element in value:
                    items.append(I18N._replace_dict(element))
                content[key] = items
            elif isinstance(value, dict):
                content[key] = I18N._replace_dict(value)

        return content

    @staticmethod
    def _process_strings(localizations: dict, **variables) -> dict:
        """Process all strings and replace general variables when loading the language file.

        A general variable is defined in one of the "general" sections of the language files.
        """
        new_dict = {}
        for locale, values in localizations.items():
            if "general" in values:
                I18N._general_values = {**values["general"], **variables}
            else:
                I18N._general_values = variables

            new_dict[locale] = I18N._replace_dict(values)

        return new_dict

    @staticmethod
    def _find_missing_keys(fallback: dict, current_locale: dict):
        """Find keys and sub-keys that are missing in the current locale."""

        missing_keys = []

        def explore_dict(original: dict, current: dict, path: str):
            for key, value in original.items():
                if key not in current:
                    missing_keys.append(f"{path}.{key}".lstrip("."))
                elif isinstance(value, dict) and isinstance(current.get(key), dict):
                    explore_dict(value, current[key], f"{path}.{key}")

        explore_dict(fallback, current_locale, "")
        return missing_keys

    @staticmethod
    def _check_localizations():
        """Checks if all locales have the same keys."""

        for locale, values in I18N.localizations.items():
            missing_keys = I18N._find_missing_keys(I18N.localizations[I18N.fallback_locale], values)
            if len(missing_keys) > 0:
                log.warn(
                    f"Locale '{locale}' misses some keys from the fallback locale: {missing_keys}"
                )
