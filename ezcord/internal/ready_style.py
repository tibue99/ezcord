"""Utility functions for the ready event."""

from __future__ import annotations

from collections import OrderedDict
from itertools import cycle, islice
from typing import TYPE_CHECKING

from colorama import Fore

from .. import __version__
from ..enums import ReadyEvent
from ..internal.dc import discord
from ..logs import log
from .colors import get_escape_code

if TYPE_CHECKING:
    from ..bot import Bot


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


def get_default_info(bot: Bot) -> list[tuple[str, str]]:
    lib_name = discord.lib.capitalize()
    try:
        ping = f"{round(bot.latency * 1000):,}ms"
    except OverflowError:
        ping = "∞"

    return [
        ("Bot", f"{bot.user}"),
        ("ID", f"{bot.user.id}"),
        (lib_name, discord.__version__),
        ("Commands", f"{bot.cmd_count:,}"),
        ("Guilds", f"{len(bot.guilds):,}"),
        ("Latency", ping),
    ]


def modify_info(
    bot: Bot, modifications: tuple, custom_color_list: list[str] | None = None
) -> tuple[list[tuple[str, str]], list[str]]:
    """Add or remove information from the default ready event."""

    infos = get_default_info(bot)
    additions, deletions = modifications
    colors = custom_color_list or DEFAULT_COLORS

    for key, settings in additions.items():
        value, position, color = settings["value"], settings["position"], settings["color"]

        if position is None:
            position = len(infos)

        infos.insert(position, (key, str(value)))
        colors.insert(position, get_escape_code(color))

    for key in deletions:
        if isinstance(key, int):
            try:
                infos.pop(key)
            except IndexError:
                log.warning(f"Index {key} does not exist and could not be removed.")
        else:
            infos = [info for info in infos if info[0] != key]

    return infos, colors


def print_custom_ready(
    bot: discord.Bot,
    title: str,
    modifications: tuple,
    style: ReadyEvent = ReadyEvent.default,
    default_info: bool = True,
    new_info: dict | None = None,
    colors: list[str] | None = None,
):
    if not bot.user:
        return log.error("The ready function must be called within the on_ready event.")

    colors = list(map(get_escape_code, colors or DEFAULT_COLORS))

    if default_info:
        infos, colors = modify_info(bot, modifications, colors)
    else:
        infos = get_default_info(bot)

    if new_info:
        for key, value in new_info.items():
            infos.append((str(key), str(value)))

    print_ready(bot, style, OrderedDict(infos), title, colors)


def print_ready(
    bot: discord.Bot,
    style: ReadyEvent,
    infos: OrderedDict | None = None,
    title: str = READY_TITLE,
    colors: list[str] | None = None,
    *,
    modifications: tuple | None = None,
    cog_status: dict[str, tuple[bool, str | None]] | None = None,
    show_cog_status: bool = True,
    show_cog_errors: bool = True,
):
    colors = colors or DEFAULT_COLORS
    infos = infos or OrderedDict(get_default_info(bot))

    if modifications:
        infos_list, colors = modify_info(bot, modifications, colors)
        infos = OrderedDict(infos_list)

    info_count = len(infos.items())
    colors = list(islice(cycle(colors), info_count))

    colon_infos = {key + ":": value for key, value in infos.items()}

    style_cls = Style()
    if "bold" in style.name:
        style_cls = Bold()

    # Create cog status table if available and enabled
    cog_table = ""
    error_list = ""
    if cog_status:
        if show_cog_status:
            cog_table = create_cog_status_table(cog_status, style_cls)
        if show_cog_errors:
            error_list = create_error_list(cog_status, style_cls)

    txt = title

    # Add cog status table before bot info
    if cog_table:
        txt += "\n" + cog_table

    if style in [ReadyEvent.box, ReadyEvent.box_bold, ReadyEvent.box_colorful]:
        txt += box(colon_infos, colors, style, style_cls)

        # Add error list after bot info
        if error_list:
            txt += error_list

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

        # Add error list after bot info
        if error_list:
            txt += error_list

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


def create_cog_status_table(
    cog_status: dict[str, tuple[bool, str | None]], s: Style = Style()
) -> str:
    """Create a table showing the loading status of all cogs.

    Parameters
    ----------
    cog_status:
        Dictionary mapping cog names to (success, error_message) tuples.
    s:
        The style of the table.

    Returns
    -------
    str
        The formatted cog status table.
    """
    if not cog_status:
        return ""

    # Create vertical table: each row = [cog_name, status]
    rows = []
    color_rows = []

    for cog_name, (success, _) in cog_status.items():
        # Show full path for subdirectories
        # Examples:
        # "cogs.example" -> "example.py"
        # "cogs.admin.moderation" -> "admin.moderation.py"
        # "ezcord.cogs.help" -> "help.py"
        # "ezcord.cogs.subdir.example" -> "subdir.example.py"
        parts = cog_name.split(".")

        # Remove common prefixes like "cogs" or "ezcord.cogs"
        if parts[0] == "cogs" and len(parts) > 1:
            # Remove "cogs" prefix
            display_name = ".".join(parts[1:]) + ".py"
        elif parts[0] == "ezcord" and len(parts) > 2 and parts[1] == "cogs":
            # Remove "ezcord.cogs" prefix
            display_name = ".".join(parts[2:]) + ".py"
        else:
            # Fallback: use last part
            display_name = parts[-1] + ".py"

        if success:
            status_plain = "   ✓   "
            status_colored = f"   {Fore.GREEN}✓{Fore.RESET}   "
        else:
            status_plain = "   ✗   "
            status_colored = f"   {Fore.RED}✗{Fore.RESET}   "

        rows.append([display_name, status_plain])
        # Explizit RESET vor dem Cog-Namen, damit keine vorherigen Farben übernommen werden
        color_rows.append([f"{Fore.RESET}{display_name}", status_colored])

    # Add header row at the beginning
    rows.insert(0, ["Cog", "Status"])
    # Header auch mit explizitem RESET
    color_rows.insert(0, [f"{Fore.RESET}Cog", f"{Fore.RESET}Status"])

    return tables_with_separators(rows, color_rows, s)


def create_error_list(cog_status: dict[str, tuple[bool, str | None]], s: Style = Style()) -> str:
    """Create a list of cogs that failed to load with their error messages.

    Parameters
    ----------
    cog_status:
        Dictionary mapping cog names to (success, error_message) tuples.
    s:
        The style of the table.

    Returns
    -------
    str
        The formatted error list.
    """
    errors = [
        (name, error) for name, (success, error) in cog_status.items() if not success and error
    ]

    if not errors:
        return ""

    # Helper function to format cog name with subdirectories
    def format_cog_name(cog_name: str) -> str:
        parts = cog_name.split(".")

        # Remove common prefixes like "cogs" or "ezcord.cogs"
        if parts[0] == "cogs" and len(parts) > 1:
            # Remove "cogs" prefix
            return ".".join(parts[1:]) + ".py"
        elif parts[0] == "ezcord" and len(parts) > 2 and parts[1] == "cogs":
            # Remove "ezcord.cogs" prefix
            return ".".join(parts[2:]) + ".py"
        else:
            # Fallback: use last part
            return parts[-1] + ".py"

    # Find the longest cog name and prepare error messages
    max_name_len = max(len(format_cog_name(name)) for name, _ in errors)
    max_error_len = 60

    # Calculate the box width based on content
    box_width = max(max_name_len + 4, len("Cog Loading Errors") + 4, max_error_len + 4)

    error_text = f"\n{s.TL}{s.H * box_width}{s.TR}\n"

    # Title centered
    title = "Cog Loading Errors"
    padding_left = (box_width - len(title)) // 2
    padding_right = box_width - len(title) - padding_left
    error_text += (
        f"{s.V}{' ' * padding_left}{Fore.RED}{title}{Fore.RESET}{' ' * padding_right}{s.V}\n"
    )
    error_text += f"{s.L}{s.H * box_width}{s.R}\n"

    for cog_name, error_msg in errors:
        display_name = format_cog_name(cog_name)

        # Cog name line
        cog_padding = box_width - len(display_name) - 2
        error_text += f"{s.V} {Fore.YELLOW}{display_name}{Fore.RESET}{' ' * cog_padding} {s.V}\n"

        # Split error message if it's too long
        error_lines = []
        words = error_msg.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_error_len:
                current_line += word + " "
            else:
                if current_line:
                    error_lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            error_lines.append(current_line.strip())

        # Error message lines
        for line in error_lines:
            line_padding = box_width - len(line) - 2
            error_text += f"{s.V} {Fore.RED}{line}{Fore.RESET}{' ' * line_padding} {s.V}\n"

        # Add separator between errors (except for last one)
        if (cog_name, error_msg) != errors[-1]:
            error_text += f"{s.L}{s.H * box_width}{s.R}\n"

    error_text += f"{s.BL}{s.H * box_width}{s.BR}"

    return error_text


def tables_with_separators(
    rows: list[list[str]], color_rows: list[list[str]] | None = None, s: Style = Style()
):
    """Create a table with separator lines between all rows (for cog status table).

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
            table += "\n" + s.L + middle_row + s.R + "\n"
        else:
            bottom_row = middle_row.replace(s.M, s.B)
            table += "\n" + s.BL + bottom_row + s.BR

    return table
