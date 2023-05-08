"""Utility functions for the ready event."""

import discord

from ..enums import ReadyEvent
from ..logs import log


async def print_ready(bot: discord.Bot, style: ReadyEvent):
    cmds = [
        cmd for cmd in bot.walk_application_commands() if type(cmd) != discord.SlashCommandGroup
    ]

    infos = {
        "User": f"{bot.user}",
        "ID": f"{bot.user.id}",
        "Pycord": discord.__version__,
        "Commands": f"{len(cmds):,}",
        "Guilds": f"{len(bot.guilds):,}",
        "Latency": f"{round(bot.latency * 1000):,}ms",
    }

    txt = f"Bot is online!"
    colon_infos = {key + ":": value for key, value in infos.items()}

    if style == ReadyEvent.box:
        txt += box(colon_infos)
        log.info(txt)
    elif style == ReadyEvent.logs:
        log.info(txt)
        logs(colon_infos)
    else:
        if style == ReadyEvent.table:
            info_list = [list(item) for item in infos.items()]
        else:
            info_list = [list(infos.keys()), list(infos.values())]
        txt += "\n" + tables(info_list)
        log.info(txt)


def box(infos):
    longest = max([str(i) for i in infos.values()], key=len)
    formatter = f"<{len(longest)}"
    longest_key = 10

    txt = f"\n╔{(len(longest) + 2 + longest_key) * '═'}╗\n"
    for key, info in infos.items():
        key = f"{key:<{longest_key}}"
        txt += f"║ {key}{info:{formatter}} ║\n"
    txt += f"╚{(len(longest) + 2 + longest_key) * '═'}╝"
    return txt


def logs(infos):
    for key, info in infos.items():
        log.info(f"{key} **{info}**")


def tables(rows: list[list[str]]):
    length = [max([len(value) for value in column]) for column in zip(*rows)]
    table = ""
    for index, row in enumerate(rows):
        table += "║"

        middle_row = ""
        for max_length, content in zip(length, row):
            space_content = f" {content} "
            table += space_content + " " * (max_length - len(content)) + "║"
            middle_row += "═" * (max_length - len(content) + len(space_content)) + "╬"

        middle_row = middle_row[:-1]
        if index == 0:
            top_row = middle_row.replace("╬", "╦")
            table = "╔" + top_row + "╗\n" + table

        if index != len(rows) - 1:
            table += "\n║" + middle_row + "║\n"
        else:
            bottom_row = middle_row.replace("╬", "╩")
            table += "\n╚" + bottom_row + "╝"

    return table
