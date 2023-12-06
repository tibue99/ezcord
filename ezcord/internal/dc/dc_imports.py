libs = ["discord", "nextcord", "disnake"]
for lib in libs:
    try:
        discord = __import__(lib)
        discord.lib = lib  # type: ignore
        break
    except ImportError:
        continue
