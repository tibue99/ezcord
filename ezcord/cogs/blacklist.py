from ..bot import Bot, Cog
from ..errors import Blacklisted
from ..internal import EzConfig, t
from ..internal.dc import discord
from ..sql import DBHandler
from ..utils import create_text_file


class BanDB(DBHandler):
    def __init__(self, db_path: str, db_name: str):
        self.db_name = db_name
        super().__init__(db_path)

    async def setup(self):
        await self.exec(
            f"""CREATE TABLE IF NOT EXISTS {self.db_name} (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            dt DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )

    async def add_ban(self, user_id: int, reason: str):
        await self.exec(
            f"INSERT INTO {self.db_name} (user_id, reason) VALUES (?, ?)", (user_id, reason)
        )

    async def remove_ban(self, user_id: int):
        await self.exec(f"DELETE FROM {self.db_name} WHERE user_id = ?", (user_id,))

    async def get_bans(self):
        return await self.all(f"SELECT user_id FROM {self.db_name}")

    async def get_full_bans(self):
        return await self.all(f"SELECT user_id, reason, dt FROM {self.db_name}")


class Blacklist(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.db = BanDB(bot.blacklist.db_path, bot.blacklist.db_name)

    async def bot_check(self, ctx):
        bans = await self.db.get_bans()
        if ctx.author.id in bans:
            if self.bot.blacklist.raise_error:
                raise Blacklisted()
            else:
                await ctx.respond(t("no_perms"), ephemeral=True)
            return False
        return True

    admin = discord.SlashCommandGroup(
        t("cmd_group_name"),
        guild_ids=EzConfig.admin_guilds,
        default_member_permissions=discord.Permissions(administrator=True),
    )

    blacklist = admin.create_subgroup("blacklist")

    @blacklist.command(name="manage", description="Manage the blacklist")
    @discord.option("choice", description="Choose an action", choices=["Add ban", "Remove ban"])
    @discord.option("user", description="The user to ban/unban")
    @discord.option("reason", description="The reason for the ban", default=None)
    async def manage_blacklist(
        self,
        ctx: discord.ApplicationContext,
        choice: str,
        user: discord.Member,
        reason: str,
    ):
        if choice == "Add ban":
            await self.db.add_ban(user.id, reason)
            await ctx.respond(
                f"The user was banned successfully.\n- **Name:** {user}\n- **ID:** {user.id}",
                ephemeral=True,
            )
        else:
            await self.db.remove_ban(user.id)
            await ctx.respond(
                f"The user **{user}** - {user.id} was unbanned successfully.", ephemeral=True
            )

    @blacklist.command(name="show", description="Show the bot blacklist")
    async def show_blacklist(self, ctx):
        await ctx.defer(ephemeral=True)
        bans = await self.db.get_full_bans()
        desc = ""

        for user_id, reason, _ in bans:
            if not reason:
                reason = "No reason provided"

            user = await self.bot.get_or_fetch_user(user_id)
            name = f"{user.name} ({user.id})" if user else user_id
            desc += f"{name} - {reason}\n"

        if not desc:
            desc = "No bans found."

        file = create_text_file(desc, "bans.txt")
        await ctx.respond(file=file, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Blacklist(bot))
