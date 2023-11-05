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
        t("admin_group"),
        guild_ids=EzConfig.admin_guilds,
        default_member_permissions=discord.Permissions(administrator=True),
    )

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        bans = await self.db.get_bans()
        if guild.owner.id in bans:
            try:
                await guild.owner.send(t("guild_error", guild.name))
            except discord.Forbidden:
                pass
            await guild.leave()

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

    @admin.command(description="Show all bot servers")
    async def show_servers(self, ctx):
        await ctx.defer(ephemeral=True)
        longest_name = max([guild.name for guild in self.bot.guilds], key=len)
        sep = f"<{len(longest_name)}"

        desc = ""
        for guild in self.bot.guilds:
            desc += f"{guild.name:{sep}} - {guild.member_count:<6,}"
            desc += f" - {guild.id}"
            desc += f" - {guild.owner} ({guild.owner.id})"
            desc += "\n"

        file = create_text_file(desc, "guilds.txt")
        await ctx.respond(file=file, ephemeral=True)

    leave = admin.create_subgroup("leave")

    @leave.command(name="server", description="Make the bot leave all guilds with a given owner")
    @discord.option("owner_id", description="Leave all servers with the specified owner")
    async def leave_guild(
        self,
        ctx: discord.ApplicationContext,
        guild_id: str,
    ):
        await ctx.defer(ephemeral=True)
        try:
            guild = await self.bot.fetch_guild(guild_id)
        except Exception as e:
            return await ctx.respond(f"I could not load this server: ```{e}```", ephemeral=True)

        await guild.leave()
        await ctx.respond(f"I left **{guild.name}** ({guild.id})", ephemeral=True)

    @leave.command(name="owner", description="Make the bot leave a guild")
    @discord.option("guild_id", description="Leave the server with the given ID", default=None)
    async def leave_owner(
        self,
        ctx: discord.ApplicationContext,
        owner: discord.User,
    ):
        await ctx.defer(ephemeral=True)
        guilds = []
        member_count = 0
        for guild in self.bot.guilds:
            if guild.owner.id == owner.id:
                guilds.append(guild)
                member_count += guild.member_count

        return await ctx.respond(
            f"I found **{len(guilds)}** servers with **{owner}** as the owner "
            f"(with a total of **{member_count}** members).",
            ephemeral=True,
            view=LeaveGuilds(guilds),
        )


def setup(bot: Bot):
    bot.add_cog(Blacklist(bot))


class LeaveGuilds(discord.ui.View):
    def __init__(self, guilds: list[discord.Guild]):
        self.guilds = guilds
        super().__init__(timeout=None)

    @discord.ui.button(label="Leave all", style=discord.ButtonStyle.red)
    async def leave(self, _: discord.ui.Button, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        embed = discord.Embed(
            description="I'll now leave all servers. This may take a while."
            "\n\nI'll ping you when I'm done.",
        )
        await interaction.edit(embed=embed, view=self)

        leave_count = 0
        for guild in self.guilds:
            try:
                await guild.leave()
                leave_count += 1
            except Exception as e:
                print(f"Could not leave guild {guild.id}: ```\n{e}```")
                continue

        await interaction.respond(
            f"{interaction.user.mention} I successfully left **{leave_count}** servers.",
            ephemeral=True,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, _: discord.ui.Button, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.edit(view=self)
