"""Inspired by Pycord: https://github.com/Pycord-Development/pycord/blob/master/discord/utils.py."""

from __future__ import annotations

import warnings


def warn_deprecated(
    name: str,
    instead: str | None = None,
    since: str | None = None,
    removed: str | None = None,
    reference: str | None = None,
    stacklevel: int = 3,
) -> None:
    """Warn about a deprecated function, with the ability to specify details about the deprecation. Emits a
    DeprecationWarning.

    Parameters
    ----------
    name: str
        The name of the deprecated function.
    instead:
        A recommended alternative to the function.
    since:
        The version in which the function was deprecated.
    removed:
        The version in which the function is planned to be removed.
    reference:
        A reference that explains the deprecation, typically a URL to a page such as a changelog entry or a GitHub
        issue/PR.
    stacklevel:
        The stacklevel kwarg passed to :func:`warnings.warn`. Defaults to ``3``.
    """
    warnings.simplefilter("always", DeprecationWarning)
    message = f"'{name}' is deprecated"
    if since:
        message += f" since version {since}"
    if removed:
        message += f" and will be removed in version {removed}"
    if instead:
        message += f", consider using '{instead}' instead"
    message += "."
    if reference:
        message += f" See {reference} for more information."

    warnings.warn(message, stacklevel=stacklevel, category=DeprecationWarning)
    warnings.simplefilter("default", DeprecationWarning)
