import ezcord

bot = ezcord.Bot(
    ready_event=None,  # Disable default ready event
)


@bot.event
async def on_ready():
    new_info = {"Custom Info": "This is a custom info"}

    bot.ready(
        title="Bot is online!",
        style=ezcord.ReadyEvent.default,
        default_info=True,
        new_info=new_info,
        colors=["red", "blue", "green"],
    )


if __name__ == "__main__":
    bot.run("TOKEN")  # Replace with your bot token
