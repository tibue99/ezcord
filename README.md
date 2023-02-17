# EzCord
[![](https://img.shields.io/discord/1010915072694046794?label=discord&style=for-the-badge&logo=discord&color=5865F2&logoColor=white)](https://discord.gg/zfvbjTEzv6)
[![](https://img.shields.io/pypi/v/ezcord.svg?style=for-the-badge&logo=pypi&color=yellow&logoColor=white)](https://pypi.org/project/ezcord/)

An easy-to-use extension for the Pycord library with a lot of utility functions.

## Installing
```
pip install ezcord
```
## Resources
- [Documentation](https://ezcord.readthedocs.io/)
- [Getting started](https://ezcord.readthedocs.io/en/latest/getting_started.html)

## Example
```py
import ezcord
import discord

bot = ezcord.Bot(
    intents=discord.Intents.default()
)

if __name__ == "__main__":
    bot.load_cogs("cogs")  # Load all cogs in the "cogs" folder
    bot.run("TOKEN")
```