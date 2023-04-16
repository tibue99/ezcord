import json
import os
from functools import cache
from pathlib import Path
from typing import Dict

from discord import Color, Embed

TEMPLATES: Dict[str, Embed] = {
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
    for name, embed in kwargs.items():
        if embed is None:
            embeds[name] = TEMPLATES[name].to_dict()
        else:
            embeds[name] = embed.to_dict()

    parent = Path(__file__).parent.absolute()
    with open(os.path.join(parent, "embeds.json"), "w") as file:
        json.dump(embeds, file, indent=2)


@cache
def load_embed(name: str) -> Embed:
    """Load an embed template from a JSON file."""
    parent = Path(__file__).parent.absolute()
    with open(os.path.join(parent, "embeds.json")) as file:
        embeds = json.load(file)

    try:
        return Embed.from_dict(embeds[name])
    except KeyError:
        raise ValueError(f"Embed template '{name}' not found.")
