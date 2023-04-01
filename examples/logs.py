import logging

from colorama import Fore
import ezcord
from ezcord import log


# add a custom log level
CUSTOM_LOG = 15
logging.addLevelName(CUSTOM_LOG, "COG")

# overwrite colors for specific log levels
colors = {
    logging.DEBUG: Fore.GREEN,
    CUSTOM_LOG: Fore.MAGENTA
}

# call this function before creating the bot
ezcord.set_log(
    log_format=ezcord.LogFormat.default,
    colors=colors
)

log.debug("This is a debug message")
log.warning("This is a warning message")

log.log(CUSTOM_LOG, "This is a message with a custom log level")

bot = ezcord.Bot()

if __name__ == "__main__":
    bot.run("TOKEN")  # Replace with your webhook URL
