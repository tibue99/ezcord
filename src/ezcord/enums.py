from enum import Enum


class LogFormat(str, Enum):
    """Presets for logging formats that can be used in :func:`set_log`.

    ``{color_start}`` and ``{color_end}`` are used to add colors to parts of the log message.
    If they are not used, the whole log message will be colored.
    """

    full_color = "[%(levelname)s] %(message)s"
    full_color_time = "[%(asctime)s] %(levelname)s: %(message)s"
    color_level = "[{color_start}%(levelname)s{color_end}] %(message)s"
    default = color_level

    def __str__(self):
        return self.value
