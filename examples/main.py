import discord

import ezcord

bot = ezcord.Bot(
    intents=discord.Intents.default(),
    error_webhook_url="WEBHOOK_URL",  # Replace with your webhook URL
    language="de",
)

if __name__ == "__main__":
    bot.load_cogs("cogs")  # Load all cogs in the "cogs" folder
    bot.run("TOKEN")  # Replace with your bot token
