import discord

import ezcord

# Connection attributes can be passed to the init method, but it's recommended to
# set them in a .env file.


class UserDB(ezcord.PGHandler):
    async def setup(self):
        """Execute a single query."""
        await self.exec(
            """CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            coins INTEGER DEFAULT 0
            )"""
        )

    async def add_coins(self, user_id, amount):
        """Execute multiple queries in one transaction."""
        async with self.pool.acquire() as con:
            await con.exec(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
            )
            await con.exec(
                "UPDATE users SET coins = users.coins + $1 WHERE user_id = $2", amount, user_id
            )

    async def get_users(self):
        """Return all result records."""
        return await self.all("SELECT * FROM users")

    async def get_one_user(self, user_id):
        """Return one result record."""
        return await self.one("SELECT * FROM users WHERE user_id = $1", user_id)


db = UserDB()


class Bot(ezcord.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())

    async def on_ready(self):
        await db.add_coins(12345, 100)
        result = await db.get_one_user(12345)
        print(result)  # <Record user_id=12345 coins=100>


if __name__ == "__main__":
    bot = Bot()
    bot.run()
