libs = ["discord", "nextcord", "disnake"]
for lib in libs:
    try:
        discord = __import__(lib)
        break
    except ImportError:
        continue
