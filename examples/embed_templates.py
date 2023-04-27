import discord

from ezcord import Bot, emb

# override the default error embed with a custom one
error_embed = discord.Embed(title="Error", color=discord.Color.orange())
error_embed.set_footer(text="This is a custom footer")

emb.set_embed_templates(error_embed=error_embed)


bot = Bot()


@bot.slash_command()
async def hey(ctx):
    await emb.error(ctx, "Error message")
    await emb.info(ctx, "Info message", title="Info Title")  # set an embed title


if __name__ == "__main__":
    bot.run("TOKEN")  # Replace with your bot token
