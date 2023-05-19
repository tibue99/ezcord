import json
import os
import traceback
from functools import cache
from pathlib import Path

import discord
from discord import Color, Embed

_TEMPLATES: dict[str, Embed] = {
    "success_embed": Embed(color=Color.green()),
    "error_embed": Embed(color=Color.red()),
    "warn_embed": Embed(color=Color.gold()),
    "info_embed": Embed(color=Color.blue()),
}


def save_embeds(**kwargs: Embed):
    """Save multiple embeds to a JSON file.

    If one of the default values is not included, a default template will be saved.
    """
    embeds = {}
    overrides = _TEMPLATES if len(kwargs) == 0 else kwargs

    for name, embed in overrides.items():
        if embed is None:
            embeds[name] = _TEMPLATES[name].to_dict()
        else:
            embeds[name] = embed.to_dict()

    parent = Path(__file__).parent.absolute()
    with open(os.path.join(parent, "embeds.json"), "w") as file:
        json.dump(embeds, file, indent=2)


@cache
def load_embed(name: str) -> Embed:
    """Load an embed template from a JSON file."""
    parent = Path(__file__).parent.absolute()
    json_path = parent.joinpath("embeds.json")
    if not json_path.exists():
        save_embeds()

    with open(os.path.join(parent, "embeds.json")) as file:
        embeds = json.load(file)

    try:
        return Embed.from_dict(embeds[name])
    except KeyError:
        if name in _TEMPLATES.keys():
            save_embeds()
            return load_embed()
        else:
            raise ValueError(f"Embed template '{name}' not found.")


def get_error_text(
    ctx: discord.ApplicationContext | discord.Interaction,
    error: Exception,
    item: discord.ui.Item | discord.ui.Modal | None = None,
):
    if item:
        if isinstance(item, discord.ui.Button) and item.label:
            location = f"- **Button:** {item.label}"
        elif ctx.type == discord.InteractionType.modal_submit:
            location = f"- **Modal:** {type(item).__name__}"
        else:
            location = f"- **Select Menu:** {type(item.view).__name__}"
    else:
        location = f"- **Command:** /{ctx.command.qualified_name}"

    error_txt = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    guild_txt = f"\n- **Guild:** {ctx.guild.name} - `{ctx.guild.id}`" if ctx.guild else ""
    user_txt = f"\n- **User:** {ctx.user} - `{ctx.user.id}`" if ctx.user else ""

    description = location + guild_txt + user_txt + f"\n```py\n{error_txt[:3500]}```"
    return description
