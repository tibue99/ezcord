from __future__ import annotations


class EzConfig:
    """A class to store configuration values.

    These values are usually set only once, but are used throughout the runtime of the bot.
    """

    lang: str = "en"
    embed_templates: dict = {}

    # Blacklist
    admin_guilds: list[int] | None = None