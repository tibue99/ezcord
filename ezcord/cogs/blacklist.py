"""
Commands to manage the bot blacklist.

This file should only be called through `bot.add_blacklist()`,
after the "blacklist" value has been set in the config.
"""

from typing import Union

import aiosqlite

from .. import emb
from ..blacklist import _BanDB
from ..bot import Bot, Cog
from ..components import event
from ..errors import Blacklisted
from ..internal import EzConfig, t
from ..internal.dc import commands, discord
from ..utils import create_text_file

_db = _BanDB()


async def _check_blacklist(
    # Pycord does not support __future__ in cogs for whatever reason
    interaction: Union[discord.Interaction, discord.ApplicationContext]
) -> bool:
    bans = await _db.get_bans()
    if interaction.user.id in bans and EzConfig.blacklist:
        if EzConfig.blacklist.raise_error:
            raise Blacklisted()
        else:
            await interaction.respond(t("no_perms"), ephemeral=True)
        return False
    return True


@event
async def view_check(interaction: discord.Interaction):
    return await _check_blacklist(interaction)


class Blacklist(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @staticmethod
    async def bot_check(ctx: discord.ApplicationContext):
        return await _check_blacklist(ctx)

    admin = discord.SlashCommandGroup(
        t("admin_group"),
        guild_ids=EzConfig.admin_guilds,
        default_member_permissions=discord.Permissions(administrator=True),
        checks=[commands.is_owner().predicate],
    )

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        bans = await _db.get_bans()
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
            if user.id == ctx.author.id:
                return await emb.error(ctx, "You can't ban yourself.")
            if user.bot:
                return await emb.error(ctx, "You can't ban a bot.")

            try:
                await _db.add_ban(user.id, reason)
            except aiosqlite.IntegrityError:
                return await emb.error(ctx, "This user is already banned.")
            await ctx.respond(
                f"The user was banned successfully.\n- **Name:** {user}\n- **ID:** {user.id}",
                ephemeral=True,
            )
        else:
            rowcount = await _db.remove_ban(user.id)
            if rowcount == 0:
                return await emb.error(ctx, "This user is not banned.")
            await ctx.respond(f"The user **{user}** was unbanned successfully.", ephemeral=True)

    @blacklist.command(name="show", description="Show the bot blacklist")
    async def show_blacklist(self, ctx):
        await ctx.defer(ephemeral=True)
        bans = await _db.get_full_bans()
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

    @leave.command(name="server", description="Make the bot leave a server")
    @discord.option("guild_id", description="Leave the server with the given ID", default=None)
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

    @leave.command(name="owner", description="Make the bot leave all guilds with a given owner")
    @discord.option("owner_id", description="Leave all servers with the specified owner")
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
