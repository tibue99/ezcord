import ezcord

bot = ezcord.Bot(
    show_cogs_status=True  # Optional, default is False; set to True to display cog status table on ready
)

if __name__ == "__main__":
    bot.load_cogs("cogs")  # Load your cogs from the folder
    bot.run("TOKEN")  # Replace with your bot token
