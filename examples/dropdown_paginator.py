import discord

import ezcord

bot = ezcord.Bot()


class Dropdown(ezcord.DropdownPaginator):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        # Edit the dropdown menu if user selects a page option
        await super().callback(interaction)

        # Do something here when the selects anything (item or page option)
        await interaction.respond("Item or page selected: " + self.values[0])

        if self.item_selected:
            # Do something here when the user selects an actual item
            await interaction.respond("Item selected: " + self.values[0])


@bot.slash_command()
async def hey(ctx):
    options = [discord.SelectOption(label=f"Item {i}") for i in range(30)]
    view = discord.ui.View(Dropdown(options))
    await ctx.respond(view=view)


if __name__ == "__main__":
    bot.run()
