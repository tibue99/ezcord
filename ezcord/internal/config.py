from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal


@dataclass
class Blacklist:
    db_path: str
    db_name: str
    raise_error: bool
    owner_only: bool
    disabled_commands: list[EzConfig.BLACKLIST_COMMANDS]
    overwrites: dict[str, Callable]


class EzConfig:
    """A class to store configuration values.

    These values are usually set only once, but are used throughout the runtime of the bot.
    """

    BLACKLIST_COMMANDS = Literal["add", "remove", "show", "owner", "server", "show_servers"]

    lang: str = "en"
    default_lang: str = "en"
    embed_templates: dict = {}

    # Blacklist
    admin_guilds: list[int] | None = None
    blacklist: Blacklist | None = None
