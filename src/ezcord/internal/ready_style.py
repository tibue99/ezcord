"""Utility functions for the ready event."""

from itertools import cycle, islice

import discord
from colorama import Fore

from .. import __version__
from ..enums import ReadyEvent
from ..logs import log
from .colors import get_escape_code


class Style:
    TL = "╭"  # top left
    TR = "╮"  # top right
    BL = "╰"  # bottom left
    BR = "╯"  # bottom right
    H = "─"  # horizontal
    V = "│"  # vertical
    M = "┼"  # middle
    L = "├"  # left
    R = "┤"  # right
    T = "┬"  # top
    B = "┴"  # bottom


class Bold(Style):
    TL, TR, BL, BR, H, V, M, L, R, T, B = "╔", "╗", "╚", "╝", "═", "║", "╬", "╠", "╣", "╦", "╩"


READY_TITLE: str = f"Bot is online with EzCord {__version__}"
DEFAULT_COLORS: list[str] = [Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.RED]


def get_default_info(bot: discord.Bot):
    cmds = [
        cmd for cmd in bot.walk_application_commands() if type(cmd) != discord.SlashCommandGroup
    ]

    infos = {
        "Bot": f"{bot.user}",
        "ID": f"{bot.user.id}",
        "Pycord": discord.__version__,
        "Commands": f"{len(cmds):,}",
        "Guilds": f"{len(bot.guilds):,}",
        "Latency": f"{round(bot.latency * 1000):,}ms",
    }

    return infos


def print_custom_ready(
    bot: discord.Bot,
    title: str,
    style: ReadyEvent = ReadyEvent.default,
    default_info: bool = True,
    new_info: dict | None = None,
    colors: list[str] | None = None,
):
    infos = get_default_info(bot) if default_info else {}
    colors = list(map(get_escape_code, colors or DEFAULT_COLORS))

    if new_info:
        for key, value in new_info.items():
            infos[key] = value

    print_ready(bot, style, infos, title, colors)


def print_ready(
    bot: discord.Bot,
    style: ReadyEvent,
    infos: dict[str, str] | None = None,
    title: str = READY_TITLE,
    colors: list[str] | None = None,
):
    infos = infos or get_default_info(bot)
    colors = colors or DEFAULT_COLORS

    info_count = len(infos.items())
    colors = list(islice(cycle(colors), info_count))

    colon_infos = {key + ":": value for key, value in infos.items()}

    style_cls = Style()
    if "bold" in style.name:
        style_cls = Bold()

    txt = title
    if style in [ReadyEvent.box, ReadyEvent.box_bold, ReadyEvent.box_colorful]:
        txt += box(colon_infos, colors, style, style_cls)
        log.info(txt)
    elif style == ReadyEvent.logs:
        log.info(txt)
        logs(colon_infos)
    else:
        color_table = {
            key: colors[i] + value + Fore.RESET for i, (key, value) in enumerate(infos.items())
        }
        if style == ReadyEvent.table or style == ReadyEvent.table_bold:
            info_list = [list(infos.keys()), list(infos.values())]
            color_list = [list(color_table.keys()), list(color_table.values())]
        else:
            info_list = [list(item) for item in infos.items()]
            color_list = [list(item) for item in color_table.items()]

        txt += f"\n{Fore.RESET}" + tables(info_list, color_list, style_cls)
        log.info(txt)


def box(infos: dict[str, str], colors: list[str], box_style: ReadyEvent, s: Style = Style()):
    longest = max([str(i) for i in infos.values()], key=len)
    formatter = f"<{len(longest)}"
    longest_key = max([len(i) for i in infos.keys()]) + 1

    if box_style == ReadyEvent.box_colorful:
        txt = f"\n{Fore.RESET}"
    else:
        txt = "\n"

    txt += f"{s.TL}{(len(longest) + 2 + longest_key) * s.H}{s.TR}\n"
    for index, (key, info) in enumerate(infos.items()):
        key = f"{key:<{longest_key}}"
        if box_style == ReadyEvent.box_colorful:
            txt += f"{s.V} {key}{colors[index]}{info:{formatter}}{Fore.RESET} {s.V}\n"
        else:
            txt += f"{s.V} {key}{info:{formatter}} {s.V}\n"
    txt += f"{s.BL}{(len(longest) + 2 + longest_key) * s.H}{s.BR}"
    return txt


def logs(infos: dict[str, str]):
    for key, info in infos.items():
        log.info(f"{key} **{info}**")


def tables(rows: list[list[str]], color_rows: list[list[str]] | None = None, s: Style = Style()):
    """Create a table from a list of rows.

    Parameters
    ----------
    rows:
        The rows of the table. This is used to calculate the length of each column.
    color_rows:
        The rows of the table with color. This is used as the actual content of the table.
        If this is None, the content of the table will be taken from ``rows``.
    s:
        The style of the table.
    """
    if color_rows is None:
        color_rows = rows

    length = [max([len(value) for value in column]) for column in zip(*rows)]
    table = ""
    for index, (row, color_row) in enumerate(zip(rows, color_rows)):
        table += s.V

        middle_row = ""
        for max_length, content, color_content in zip(length, row, color_row):
            space_content = f" {content} "
            color_space_content = f" {color_content} "
            table += color_space_content + " " * (max_length - len(content)) + s.V
            middle_row += s.H * (max_length - len(content) + len(space_content)) + s.M

        middle_row = middle_row[:-1]
        if index == 0:
            top_row = middle_row.replace(s.M, s.T)
            table = s.TL + top_row + s.TR + "\n" + table

        if index != len(rows) - 1:
            table += "\n" + s.V + middle_row + s.V + "\n"
        else:
            bottom_row = middle_row.replace(s.M, s.B)
            table += "\n" + s.BL + bottom_row + s.BR

    return table
