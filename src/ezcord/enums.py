from enum import Enum


class LogFormat(str, Enum):
    """Presets for logging formats that can be used in :func:`set_log`.

    ``{color}`` and ``{color_end}`` are used to add colors to parts of the log message.
    If they are not used, the whole log message will be colored.

    ``//`` at the end of the log format is used to indicate that new lines will be fully colored.
    """

    full_color = "[%(levelname)s] %(message)s"
    full_color_time = "[%(asctime)s] %(levelname)s: %(message)s"
    color_level = "[{color}%(levelname)s{color_end}] %(message)s"
    color_level_time = (
        "[{color}%(asctime)s{color_end}] [{color}%(levelname)s{color_end}] %(message)s"
    )
    default = "[{color}%(levelname)s{color_end}] %(message)s//"

    def __str__(self):
        return self.value


class ReadyEvent(Enum):
    """Styles for the ready event."""

    box = 0
    box_bold = 1
    logs = 2
    table = 3
    table_bold = 4
    table_vertical = 5
    table_vertical_bold = 6
    default = table

    def __str__(self):
        return self.name
