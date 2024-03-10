"""Embed templates that can be used to send messages.
These functions will generate embeds and send them to the desired target.

Example
-------
Here is an example for sending a success message within a Pycord application command.

.. code-block:: python

    import ezcord

    bot = ezcord.Bot()

    @bot.slash_command()
    async def hey(ctx: ezcord.EzContext):
        await ctx.success("Success!")

In any other case, the interaction must be passes to the template method.

.. code-block:: python

    class ExampleView(discord.ui.View):
        @discord.ui.button(label="Click here")
        async def button_callback(self, button, interaction):
            await emb.success(interaction, "Success!")
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from .i18n import I18N, t
from .internal import load_embed, replace_dict, save_embeds
from .internal.dc import PYCORD, discord

if PYCORD:
    _INTERACTION = (discord.Interaction, discord.ApplicationContext)
    _ctx_type = discord.ApplicationContext
else:
    _INTERACTION = (discord.Interaction,)  # type: ignore
    _ctx_type = discord.Interaction

if TYPE_CHECKING:
    import discord  # type: ignore

    _ctx_type = discord.ApplicationContext


def set_embed_templates(
    *,
    error_embed: discord.Embed | str | None = None,
    success_embed: discord.Embed | str | None = None,
    warn_embed: discord.Embed | str | None = None,
    info_embed: discord.Embed | str | None = None,
    **kwargs: discord.Embed,
):
    """Override the default embeds with custom ones.

    This must be called before the first embed template is used. The description
    of the embeds will be replaced with the given text.

    If you pass a string, error messages will be sent as a text instead of an embed.
    If the string is empty, the text will be taken from template methods.

    .. note::
        You can use the following variables for embed templates. They will automatically
        be replaced when the template is sent to an interaction.

        - ``{user}`` - The user who initiated the interaction
        - ``{username}`` - The name of the user
        - ``{user_mention}`` - The user mention
        - ``{user_id}`` - The ID of the user
        - ``{user_avatar}`` - The URL of the user's avatar

        Server variables will be replaced with information about the bot if the interaction
        was initiated in DMs.

        - ``{servername}`` - The guild where the interaction was initiated
        - ``{server_icon}`` - The URL of the guild's icon

        Bot variables will be replaced with information about the bot.

        - ``{guild_count}`` - Number of servers the bot is in
        - ``{user_count}`` - Number of users the bot can see
        - ``{cmd_count}`` - Number of application commands

    Parameters
    ----------
    error_embed:
        The embed to use for error messages.
    success_embed:
        The embed to use for success messages.
    warn_embed:
        The embed to use for warning messages.
    info_embed:
        The embed to use for info messages.
    **kwargs:
        Additional embed templates. Can be used with :func:`send`.

    Example
    -------
    .. code-block:: python

        from ezcord import emb

        embed = discord.Embed(
            title="Error",
            color=discord.Color.orange()
        )
        emb.set_embed_templates(error_embed=embed)
    """
    save_embeds(
        error_embed=error_embed,
        success_embed=success_embed,
        warn_embed=warn_embed,
        info_embed=info_embed,
        **kwargs,
    )


async def _send_embed(
    target: discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed | str,
    ephemeral: bool = True,
    edit: bool = False,
    **kwargs,
):
    """Respond to an interaction or send an embed to a target.

    If the interaction has already been responded to,
    the message will be sent as a followup.
    """
    content = None
    if isinstance(embed, str):
        content = embed
        embed = None

    if "content" in kwargs:
        content = kwargs.pop("content")

    if not isinstance(target, _INTERACTION):
        return await target.send(content=content, embed=embed, **kwargs)

    if PYCORD and isinstance(target, discord.ApplicationContext):
        target = target.interaction

    if edit:
        if not target.response.is_done():
            return await target.response.edit_message(content=content, embed=embed, **kwargs)
        else:
            return await target.edit_original_response(content=content, embed=embed, **kwargs)

    if not target.response.is_done():
        return await target.response.send_message(
            content=content, embed=embed, ephemeral=ephemeral, **kwargs
        )
    else:
        if I18N.initialized:
            return await target.followup.send(
                content=content, embed=embed, ephemeral=ephemeral, use_locale=target, **kwargs
            )
        else:
            return await target.followup.send(
                content=content, embed=embed, ephemeral=ephemeral, **kwargs
            )


def _insert_info(
    target: discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed | str,
):
    if not isinstance(target, _INTERACTION):
        return embed

    interaction = target
    if PYCORD:
        if isinstance(target, discord.ApplicationContext):
            interaction = target.interaction

    if isinstance(embed, discord.Embed):
        embed = embed.to_dict()
    embed_dic = replace_dict(embed, interaction)

    if isinstance(embed, dict):
        return discord.Embed.from_dict(embed_dic)

    return embed_dic


async def _process_message(
    target: discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed | str,
    txt: str | None,
    title: str | None,
    edit: bool,
    ephemeral: bool,
    **kwargs,
):
    if isinstance(embed, discord.Embed):
        embed = copy.deepcopy(embed)
        if txt is not None:
            embed.description = txt
        if title is not None:
            embed.title = title
    elif isinstance(embed, str) and embed == "":
        embed = txt

    embed = _insert_info(target, embed)

    return await _send_embed(target, embed, ephemeral, edit, **kwargs)


def _template_docstring(params=False):
    def decorator(func, *args, **kwargs):
        func.__doc__ += """

        Parameters
        ----------
        """

        if params:
            func.__doc__ += """
        template:
            The name of the template that was used in :func:`set_embed_templates`.
        """

        func.__doc__ += """
        target:
            The target to send the message to.
        txt:
            The text for the embed description. If this is ``None``,
            you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
        title:
            The title of the embed. Defaults to ``None``.
        edit:
            Whether to edit the last message instead of sending a new one. Defaults to ``False``.
        ephemeral:
            Whether the message should be ephemeral. Defaults to ``True``.
        **kwargs:
            Additional keyword arguments for :meth:`discord.abc.Messageable.send`.

        Returns
        -------
        :class:`discord.Interaction` | :class:`discord.Message` | ``None``
        """
        return func

    return decorator


@_template_docstring()
async def error(
    target: discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
    *,
    title: str | None = None,
    edit: bool = False,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an error message. By default, this is a red embed."""
    embed = load_embed("error_embed")
    return await _process_message(target, embed, txt, title, edit, ephemeral, **kwargs)


@_template_docstring()
async def success(
    target: discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
    *,
    title: str | None = None,
    edit: bool = False,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a success message. By default, this is a green embed."""
    embed = load_embed("success_embed")
    return await _process_message(target, embed, txt, title, edit, ephemeral, **kwargs)


@_template_docstring()
async def warn(
    target: discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
    *,
    title: str | None = None,
    edit: bool = False,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a warning message. By default, this is a golden embed."""
    embed = load_embed("warn_embed")
    return await _process_message(target, embed, txt, title, edit, ephemeral, **kwargs)


@_template_docstring()
async def info(
    target: discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
    *,
    title: str | None = None,
    edit: bool = False,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an info message. By default, this is a blue embed."""
    embed = load_embed("info_embed")
    return await _process_message(target, embed, txt, title, edit, ephemeral, **kwargs)


@_template_docstring(params=True)
async def send(
    template: str,
    target: discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
    *,
    title: str | None = None,
    edit: bool = False,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a custom embed template. This needs to be set up with :func:`set_embed_templates`."""
    embed = load_embed(template)
    return await _process_message(target, embed, txt, title, edit, ephemeral, **kwargs)


class EzContext(_ctx_type):  # type: ignore
    """A custom context to access embed templates. Only works within Pycord application commands."""

    async def error(self, msg: str, **kwargs):
        return await error(self, msg, **kwargs)

    async def success(self, msg: str, **kwargs):
        return await success(self, msg, **kwargs)

    async def warn(self, msg: str, **kwargs):
        return await warn(self, msg, **kwargs)

    async def info(self, msg: str, **kwargs):
        return await info(self, msg, **kwargs)

    def t(self, key: str, count: int | None = None, **kwargs):
        return t(self.interaction, key, count, **kwargs)
