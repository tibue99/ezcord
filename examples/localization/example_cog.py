import discord
from discord.commands import slash_command

import ezcord


class ExampleCog(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def command1(self, ctx: ezcord.EzContext):
        embed = ezcord.TEmbed("command1.embed1", color=discord.Color.blurple())
        await ctx.respond("command1.welcome", embed=embed, user=ctx.user.mention)


def setup(bot):
    bot.add_cog(ExampleCog(bot))
