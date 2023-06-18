import ezcord


class UserDB(ezcord.DBHandler):
    def __init__(self):
        super().__init__("user.db")

    async def setup(self):
        """Execute a single query."""
        await self.exec(
            """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
            )"""
        )

    async def add_coins(self, user_id, amount):
        """Execute multiple queries in one transaction."""
        transaction = self.start()
        await transaction.exec("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await transaction.exec(
            "UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id), end=True
        )
        # Alternative to end=True:
        # await transaction.close()

    async def get_users(self):
        """Return all result rows."""
        return await self.all("SELECT * FROM users")

    async def get_one_user(self, user_id):
        """Return one result row."""
        return await self.one("SELECT * FROM users WHERE user_id = ?", (user_id,))
