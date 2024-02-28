import yaml

import ezcord

with open("commands.yaml", encoding="utf-8") as file:
    localizations = yaml.safe_load(file)

with open("en.yaml", encoding="utf-8") as file:
    en = yaml.safe_load(file)

string_locals = {"en": en}
ezcord.i18n.I18N(string_locals)

if __name__ == "__main__":
    bot = ezcord.Bot()
    bot.load_cogs()
    bot.localize_commands(localizations)  # Must be called after all commands and cogs are loaded
    bot.run()
