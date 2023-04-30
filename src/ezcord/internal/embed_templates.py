import json
import os
from functools import cache
from pathlib import Path

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
