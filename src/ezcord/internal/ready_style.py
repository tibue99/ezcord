"""Utility functions for the ready event."""

import discord

from ..enums import ReadyEvent
from ..logs import log


async def print_ready(bot: discord.Bot, style: ReadyEvent):
    cmds = [
        cmd for cmd in bot.walk_application_commands() if type(cmd) != discord.SlashCommandGroup
    ]

    infos = {
        "User:": f"{bot.user}",
        "ID:": f"{bot.user.id}",
        "Pycord:": discord.__version__,
        "Commands:": f"{len(cmds):,}",
        "Guilds:": f"{len(bot.guilds):,}",
        "Latency:": f"{round(bot.latency * 1000):,}ms",
    }

    txt = f"{bot.user} is online!"

    if style == ReadyEvent.box:
        txt += box(infos)
        log.info(txt)
    elif style == ReadyEvent.logs:
        log.info(txt)
        logs(infos)


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
