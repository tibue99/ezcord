from __future__ import annotations

import inspect
import traceback
from copy import deepcopy
from functools import cache
from typing import Callable

from ..internal.dc import discord
from .config import EzConfig


def _get_templates() -> dict[str, discord.Embed]:
    return {
        "success_embed": discord.Embed(color=discord.Color.green()),
        "error_embed": discord.Embed(color=discord.Color.red()),
        "warn_embed": discord.Embed(color=discord.Color.gold()),
        "info_embed": discord.Embed(color=discord.Color.blue()),
    }


def save_embeds(**kwargs: discord.Embed | str):
    """Save embeds to config.

    If one of the default values is not included, a default template will be saved.
    """
    embeds = {}
    overrides = _get_templates() if len(kwargs) == 0 else kwargs

    for name, embed in overrides.items():
        if embed is None:
            embeds[name] = _get_templates()[name].to_dict()
        elif isinstance(embed, str):
            embeds[name] = embed
        else:
            embeds[name] = embed.to_dict()

    EzConfig.embed_templates = embeds


@cache
def load_embed(name: str) -> discord.Embed | str:
    """Load an embed template."""

    if not EzConfig.embed_templates:
        save_embeds()

    embeds = EzConfig.embed_templates

    if isinstance(embeds[name], str):
        return embeds[name]

    try:
        return discord.Embed.from_dict(embeds[name])
    except KeyError:
        if name in _get_templates().keys():
            save_embeds()
            return load_embed()
        else:
            raise ValueError(f"Embed template '{name}' not found.")


def format_error(error: Exception) -> str:
    txt = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    return f"\n```py\n{txt[:3500]}```"


def get_error_text(
    ctx,
    error: Exception,
    item: discord.ui.Item | discord.ui.Modal | None = None,
):
    """Get the description for the webhook embed."""
    if item:
        if isinstance(item, discord.ui.Button) and item.label:
            location = f"- **Button:** {item.label}"
        elif ctx.type == discord.InteractionType.modal_submit:
            location = f"- **Modal:** {type(item).__name__}"
        else:
            location = f"- **Select Menu:** {type(item.view).__name__}"
    else:
        location = f"- **Command:** /{ctx.command.qualified_name}"

    guild_txt = f"\n- **Guild:** {ctx.guild.name} - `{ctx.guild.id}`" if ctx.guild else ""
    user_txt = f"\n- **User:** {ctx.user} - `{ctx.user.id}`" if ctx.user else ""

    description = location + guild_txt + user_txt + format_error(error)
    return description


def get_bot_values(bot: discord.Client) -> dict[str, str]:
    return {
        "guild_count": str(len(bot.guilds)),
        "user_count": str(len(bot.users)),
        "cmd_count": str(bot.cmd_count),
    }


def replace_values(
    s: str, interaction: discord.Interaction, custom_dict: dict[str, str] | None = None
) -> str:
    user = interaction.user

    replace = {
        "user": f"{user}",
        "username": user.name,
        "user_mention": user.mention,
        "user_id": f"{user.id}",
        "user_avatar": user.display_avatar.url,
        **get_bot_values(interaction.client),
    }
    if custom_dict:
        replace = {**replace, **custom_dict}

    if interaction.guild:
        replace["servername"] = interaction.guild.name
    else:
        replace["servername"] = interaction.client.user.name

    if interaction.guild and interaction.guild.icon:
        replace["server_icon"] = interaction.guild.icon.url
    else:
        replace["server_icon"] = interaction.client.user.display_avatar.url

    for key, value in replace.items():
        s = s.replace("{" + key + "}", str(value))

    return s


def replace_dict(
    content: dict | str, interaction: discord.Interaction, custom_dict: dict[str, str] | None = None
) -> dict | str:
    """Recursively loop through a dictionary and replace certain values
    with information from the current interaction.
    """
    if isinstance(content, str):
        return replace_values(content, interaction, custom_dict)

    for key, value in content.items():
        if isinstance(value, str):
            content[key] = replace_values(value, interaction, custom_dict)
        elif isinstance(value, list):
            items = []
            for element in value:
                items.append(replace_dict(element, interaction, custom_dict))
            content[key] = items
        elif isinstance(value, dict):
            content[key] = replace_dict(value, interaction, custom_dict)

    return content


def replace_embed_values(
    embed: discord.Embed,
    interaction: discord.Interaction,
    custom_dict: dict[str, str] | None = None,
):
    embed_dict = deepcopy(embed).to_dict()
    embed_dict = replace_dict(embed_dict, interaction, custom_dict)
    return discord.Embed.from_dict(embed_dict)


async def fill_custom_variables(custom_vars: dict[str, Callable | str]) -> dict[str, str]:
    """Loop through custom variables that were given as kwargs and replace them with
    their current value.
    """
    new_custom_vars = {}

    for key, value in custom_vars.items():
        if inspect.iscoroutinefunction(value):
            replace_value = await value()
        elif callable(value):
            replace_value = value()
        else:
            replace_value = value

        new_custom_vars[key] = str(replace_value)

    return new_custom_vars
