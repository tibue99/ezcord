class EzcordException(Exception):
    """Base exception class for all Ezcord exceptions."""


class MissingDiscordLibrary(EzcordException):
    """Raised when no discord library is found."""

    def __init__(self):
        super().__init__("No discord library found. Please install a supported library.")
