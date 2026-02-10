import ezcord

bot = ezcord.Bot()

if __name__ == "__main__":
    bot.load_cogs(
        "cogs",
        log=ezcord.CogLog.table,  # Shows a cog status table that matches the ready event style
    )
    bot.run("TOKEN")  # Replace with your bot token
