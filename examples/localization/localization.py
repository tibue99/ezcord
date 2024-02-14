import yaml

import ezcord

with open("example_en.yml", encoding="utf-8") as file:
    en = yaml.safe_load(file)

string_locals = {"en": en}
ezcord.i18n.I18N(string_locals)

if __name__ == "__main__":
    bot = ezcord.Bot()
    bot.load_cogs()
    bot.run()
