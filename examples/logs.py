import logging

from colorama import Fore

import ezcord
from ezcord import log

# overwrite colors for specific log levels
# this can be done with strings or with colorama
colors = {
    logging.DEBUG: "blue",
    logging.INFO: Fore.MAGENTA,
}

# call this function before creating the bot
ezcord.set_log(
    log_format=ezcord.LogFormat.default,
    colors=colors,
    webhook_url="WEBHOOK_URL",  # Replace with your webhook URL
)

log.debug("This is a debug message")
log.info("This is an info message")

ezcord.custom_log("CUSTOM", "This is a message with a custom log level")

bot = ezcord.Bot()

if __name__ == "__main__":
    bot.load_cogs("cogs", custom_logs="magenta")  # Load all cogs with a custom log color
    bot.run("TOKEN")  # Replace with your bot token
