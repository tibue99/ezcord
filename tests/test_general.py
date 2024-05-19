import os
import tempfile

import pytest

import ezcord
from ezcord.internal.dc import discord


class UserDB(ezcord.DBHandler):
    def __init__(self, path):
        super().__init__(path)

    async def setup(self):
        await self.exec(
            """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
            )"""
        )

    async def add_coins(self, user_id, amount):
        async with self.start() as cursor:
            await cursor.exec("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await cursor.exec(
                "UPDATE users SET coins = coins + ? WHERE user_id = ?",
                (amount, user_id),
            )

    async def get_users(self):
        return await self.all("SELECT user_id FROM users")

    async def get_coins(self, user_id):
        return await self.one("SELECT coins FROM users WHERE user_id = ?", (user_id,))


@pytest.mark.dc
def test_libs():
    """Test compatibility with different Discord libraries."""

    intents = discord.Intents.default()
    intents.message_content = True
    bot = ezcord.Bot(command_prefix="!", intents=intents)

    assert bot
    with pytest.raises(TypeError):
        bot.run()


@pytest.mark.asyncio
async def test_db():
    """Test the DBHandler class."""

    with tempfile.NamedTemporaryFile(delete=False) as db_file:
        db = UserDB(db_file.name)

        await db.setup()
        await db.add_coins(12345, 100)

        assert await db.get_coins(12345) == 100

        await db.add_coins(54321, 0)
        assert await db.get_users() == [12345, 54321]

    if db_file.name:
        os.remove(db_file.name)
