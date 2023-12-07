import ezcord

bot = ezcord.Bot(
    ready_event=None,  # Disable default ready event
)


@bot.event
async def on_ready():
    bot.remove_ready_info("Guilds")  # Remove an information
    bot.remove_ready_info(0)  # Remove the first information

    # Add an information at the end
    bot.add_ready_info("Title", "This is a custom info")

    # Add an information at the first position with a custom color
    bot.add_ready_info("Title", "This is another custom info", 0, "red")

    bot.ready(
        title="Bot is online!",
        style=ezcord.ReadyEvent.default,
    )


if __name__ == "__main__":
    bot.run("TOKEN")  # Replace with your bot token
