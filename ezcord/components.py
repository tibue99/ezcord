"""Classes that are adding some functionality for default components.

.. hint::

        Components in your code are automatically replaced with the ones from this module.
        You can use `discord.ui.View` instead of `ezcord.View`.
"""

from __future__ import annotations

import asyncio
import inspect
import os
from typing import Callable

import aiohttp

from .errors import ErrorMessageSent
from .internal import get_error_text
from .internal.dc import PYCORD, discord
from .logs import log
from .utils import warn_deprecated

_view_error_handlers: list[Callable] = []
_view_checks: list[Callable] = []
_view_check_failures: list[Callable] = []
_modal_error_handlers: list[Callable] = []

__all__ = ("event", "Modal", "View", "EzView", "EzModal", "DropdownPaginator")


def _check_coro(func):
    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"Event registered must be a coroutine function, not {type(func)}")


def _check_params(func, amount):
    parameters = inspect.signature(func).parameters
    if len(parameters) != amount:
        raise ValueError(
            f"Event method must have '{amount}' parameters, has '{len(parameters)}' instead"
        )


def event(coro):
    """A decorator to register custom checks and error handlers for Discord components.

    Example
    -------
    .. code-block:: python

        @ezcord.event
        async def view_check(interaction):
            return interaction.user.id == 12345  # Returns True or False

        @ezcord.event
        async def on_view_check_failure(interaction):
            await interaction.response.send_message("You can't use this!")

        @ezcord.event
        async def on_view_error(error, item, interaction):
            await interaction.response.send_message("Something went wrong!")

        @ezcord.event
        async def on_modal_error(error, interaction):
            await interaction.response.send_message("Something went wrong!")
    """
    _check_coro(coro)

    name = coro.__name__.lstrip("_")

    if name == "view_check":
        _check_params(coro, 1)
        _view_checks.append(coro)
    elif name == "on_view_check_failure":
        _check_params(coro, 1)
        _view_check_failures.append(coro)
    elif name == "on_view_error":
        _check_params(coro, 3)
        _view_error_handlers.append(coro)
    elif name == "on_modal_error":
        _check_params(coro, 2)
        _modal_error_handlers.append(coro)
    else:
        raise ValueError(f"Invalid event name: '{coro.__name__}'")

    log.debug(f"Registered event **{coro.__name__}**")


async def _send_error_webhook(interaction, description) -> bool:
    error_webhook_url = os.getenv("ERROR_WEBHOOK_URL")
    if error_webhook_url is None:
        return False

    webhook_sent = False
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(error_webhook_url, session=session)

        embed = discord.Embed(
            title="Error Report",
            description=description,
            color=discord.Color.red(),
        )
        try:
            await webhook.send(
                embed=embed,
                username=f"{interaction.client.user.name} Error Report",
                avatar_url=interaction.client.user.display_avatar.url,
            )
        except discord.HTTPException:
            log.error(
                "Error while sending error report to webhook. "
                "Please check if the URL is correct."
            )
        else:
            webhook_sent = True

    return webhook_sent


class View(discord.ui.View):
    """This class extends from :class:`discord.ui.View` and adds some functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_error(
        self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction
    ) -> None:
        """Sends an error message to a webhook, if the URL was passed in :class:`.Bot`.

        Executes all registered error handlers with the ``@ezcord.event`` decorator.
        """
        if type(error) is ErrorMessageSent:
            return

        if not PYCORD:
            error, item, interaction = item, interaction, error

        description = get_error_text(interaction, error, item)
        webhook_sent = await _send_error_webhook(interaction, description)

        log.exception(
            f"Error in View **{type(item.view).__name__}** ```{error}```",
            exc_info=error,
            extra={"webhook_sent": webhook_sent},
        )

        for error_coro in _view_error_handlers:
            await error_coro(error, item, interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Returns ``True`` if all custom checks return ``True`` or if no custom checks are registered."""
        for coro in _view_checks:
            if not await coro(interaction):
                return False
        return True

    async def on_check_failure(self, interaction: discord.Interaction) -> None:
        """This method is called if :meth:`interaction_check` returns ``False``."""
        for coro in _view_check_failures:
            await coro(interaction)

    async def on_timeout(self) -> None:
        """If ``disable_on_timeout`` is set to ``True``, this will disable all components,
        unless the viw has been explicitly stopped.
        """
        try:
            return await super().on_timeout()
        except discord.NotFound:
            return


class Modal(discord.ui.Modal):
    """This class extends from :class:`discord.ui.Modal` and adds an error handler."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        """Sends an error message to a webhook, if the webhook URL was passed into :class:`.Bot`.

        Executes all registered error handlers with the ``@ezcord.event`` decorator.
        """
        if type(error) is ErrorMessageSent:
            return

        if not PYCORD:
            error, interaction = interaction, error

        description = get_error_text(interaction, error, self)
        webhook_sent = await _send_error_webhook(interaction, description)

        log.exception(
            f"Error in Modal **{type(self).__name__}**",
            exc_info=error,
            extra={"webhook_sent": webhook_sent},
        )

        for error_coro in _modal_error_handlers:
            await error_coro(error, interaction)


class EzView(View):
    """Alias for :class:`View`."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warn_deprecated("ezcord.EzView", "discord.ui.View", "2.6")


class EzModal(Modal):
    """Alias for :class:`Modal`."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warn_deprecated("ezcord.EzModal", "discord.ui.Modal", "2.6")


# replace all default components with Ezcord components
discord.ui.View = View
discord.ui.Modal = Modal


class DropdownPaginator(discord.ui.Select):
    """A dropdown paginator that can be used to paginate through a list of options.

    Parameters
    ----------
    options
        The options that will be displayed in the dropdown.
    page: int
        The current page of the dropdown.
    """

    def __init__(
        self,
        options: list[discord.SelectOption],
        next_page_label: str = "Next page",
        previous_page_label: str = "Previous page",
        next_page_emoji: str = "➡️",
        previous_page_emoji: str = "⬅️",
        page: int = 0,
        **kwargs,
    ):
        self.page = page

        self.next_page_label = next_page_label
        self.previous_page_label = previous_page_label
        self.next_page_emoji = next_page_emoji
        self.previous_page_emoji = previous_page_emoji

        self.total_options = options
        self.current_options = self.load_options(options, self.page)
        self.kwargs = kwargs

        super().__init__(options=self.current_options, **kwargs)

    async def callback(self, interaction: discord.Interaction):

        def kek(x):
            if isinstance(x, DropdownPaginator):
                self.options = self.current_options
                return self
            else:
                return x

        if self.check_next_page():
            test = map(kek, self.view.children)

            self.view.children = list(test)
            await interaction.response.edit_message(view=self.view)
            return

        elif self.check_previous_page():
            test = map(kek, self.view.children)

            self.view.children = list(test)
            await interaction.response.edit_message(view=self.view)
            return

    def check_next_page(self) -> bool:
        """Returns True if the user clicked on the next page button.
        In this case, the dropdown menu will be edited.
        """
        if "ez_next" in self.values:
            self.page += 1
            self.current_options = self.load_options(self.total_options, self.page)
            return True
        return False

    def check_previous_page(self) -> bool:
        if "ez_previous" in self.values:
            self.page -= 1
            self.current_options = self.load_options(self.total_options, self.page)
            return True
        return False

    def load_options(
        self, options: list[discord.SelectOption], chunk: int = 0
    ) -> list[discord.SelectOption]:
        chunk_size = 23
        if len(options) > chunk_size:
            # split list into chunks
            x = [
                options[option : option + chunk_size]
                for option in range(0, len(options), chunk_size)
            ]

            new_options = x[chunk]
            if len(new_options) == chunk_size:
                new_options.append(
                    discord.SelectOption(
                        label=self.next_page_label, value="ez_next", emoji=self.next_page_emoji
                    )
                )

            if chunk > 0:
                new_options.insert(
                    0,
                    discord.SelectOption(
                        label=self.previous_page_label,
                        value="ez_previous",
                        emoji=self.previous_page_emoji,
                    ),
                )
        else:
            new_options = options

        return new_options
