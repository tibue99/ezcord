import discord
from discord.commands import slash_command

import ezcord


class ExampleCog(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def example_cmd(self, ctx: ezcord.EzContext):
        # Keys from the language file will be auto-translated.
        await ctx.respond("example.command1.welcome", user=ctx.user.mention)

        # You can use multiple keys and other values in the same string.
        await ctx.respond("🍪 {example.command1.welcome}", user=ctx.user.mention)

        # Strings can also be loaded directly.
        text = ctx.t("example.command1.welcome", user=ctx.user.mention)
        await ctx.respond(text)

        # If ctx is not available, you can use other types to determine the language.
        text = ezcord.t(ctx.interaction, "example.command1.welcome", user=ctx.user.mention)
        await ctx.respond(text)

        # The count variable is used for pluralization.
        await ctx.respond("🍪 {example.command1.welcome_cookie}", count=1)

        # Keys can be used in other places as well.
        embed = discord.Embed(title="example.command1.welcome")
        view = discord.ui.View(discord.ui.Button(label="example.command1.welcome"))
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(ExampleCog(bot))
