from .internal.dc import DPY, discord

if DPY:
    _DC_ERROR_TYPE = discord.app_commands.AppCommandError
else:
    _DC_ERROR_TYPE = discord.DiscordException


class ErrorMessageSent(_DC_ERROR_TYPE):  # type: ignore
    """Exception that can be raised to indicate that an error message has already been sent to the user.

    This could be useful if an error message has already been sent to the user within a check
    function. This prevents further messages to the user, as this error will be ignored by
    the default error handler.
    """


class EzcordException(Exception):
    """Base exception class for all Ezcord exceptions."""


class ConvertTimeError(EzcordException):
    """Raised when a time conversion fails."""


class Blacklisted(EzcordException):
    """Can be raised when a blacklisted user tries to use a command.

    This error can be caught in a command error handler to send a custom response.
    """
