class EzcordException(Exception):
    """Base exception class for all Ezcord exceptions."""


class MissingDiscordLibrary(EzcordException):
    """Raised when no discord library is found."""

    def __init__(self):
        super().__init__("No discord library found. Please install a supported library.")


class ConvertTimeError(EzcordException):
    """Raised when a time conversion fails."""


class Blacklisted(EzcordException):
    """Can be raised when a blacklisted user tries to use a command.

    This error can be caught in a command error handler to send a custom response.
    """
