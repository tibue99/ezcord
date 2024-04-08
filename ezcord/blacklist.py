"""
The blacklist can be managed within Discord using the ``/admin`` commands.
However, if you want to manage the blacklist in your own code, you can use these functions.

.. warning::

    These methods can only be used after the blacklist has been activated with :meth:`.add_blacklist`.
"""

from __future__ import annotations

from .internal import EzConfig
from .sql import DBHandler


class _BanDB(DBHandler):
    def __init__(self):
        self.db_name = EzConfig.blacklist.db_name
        super().__init__(EzConfig.blacklist.db_path)

    async def setup(self):
        await self.exec(
            f"""CREATE TABLE IF NOT EXISTS {self.db_name} (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )

    async def add_ban(self, user_id: int, reason: str | None):
        await self.exec(
            f"INSERT INTO {self.db_name} (user_id, reason) VALUES (?, ?)", (user_id, reason)
        )

    async def remove_ban(self, user_id: int):
        result = await self.exec(f"DELETE FROM {self.db_name} WHERE user_id = ?", (user_id,))
        return result.rowcount

    async def get_bans(self):
        return await self.all(f"SELECT user_id FROM {self.db_name}")

    async def get_full_bans(self):
        return await self.all(
            f"SELECT user_id, reason, dt FROM {self.db_name} ORDER BY dt DESC",
            detect_types=1,
        )


def _blacklist_ready() -> bool:
    if not EzConfig.blacklist:
        return False
    return True


async def get_bans() -> list[int]:
    """Get all banned user IDs."""
    if not _blacklist_ready():
        return []
    return await _BanDB().get_bans()


async def get_full_bans() -> list[tuple[int, str | None, str]]:
    """Get all information about banned users.

    Returns
    -------
        A list of tuples containing the user ID, ban reason, and date of the ban.
    """
    if not _blacklist_ready():
        return []
    return await _BanDB().get_full_bans()


async def add_ban(user_id: int, reason: str | None = None) -> bool:
    """Ban a user.

    Parameters
    ----------
    user_id:
        The user ID to ban
    reason:
        The reason for the ban

    Returns
    -------
    bool:
        True if the user was banned successfully, False otherwise
    """
    if not _blacklist_ready():
        return False
    await _BanDB().add_ban(user_id, reason)
    return True


async def remove_ban(user_id: int) -> bool:
    """Unban a user.

    Parameters
    ----------
    user_id:
        The user ID to unban

    Returns
    -------
    bool:
        True if the user was unbanned successfully, False otherwise
    """
    if not _blacklist_ready():
        return False
    result = await _BanDB().remove_ban(user_id)
    return bool(result)
