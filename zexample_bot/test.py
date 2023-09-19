import ezcord
from ezcord.internal.dc import discord

intents = discord.Intents.default()
intents.message_content = True

bot = ezcord.Bot(command_prefix="!", intents=intents)


bot.run()
