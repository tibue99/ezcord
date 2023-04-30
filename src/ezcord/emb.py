"""Embed templates that can be used to send messages.
These functions will generate embeds and send them to the desired target.

Example
-------
.. code-block:: python

    from ezcord import Bot, emb

    bot = Bot()

    @bot.slash_command()
    async def hey(ctx):
        await emb.success(ctx, "Success!")
"""

from __future__ import annotations

import discord

from .internal import copy_kwargs, load_embed, save_embeds


def set_embed_templates(
    *,
    error_embed: discord.Embed | None = None,
    success_embed: discord.Embed | None = None,
    warn_embed: discord.Embed | None = None,
    info_embed: discord.Embed | None = None,
    **kwargs: discord.Embed,
):
    """Override the default embeds with custom ones.

    This must be called before the first embed template is used. The description
    of the embeds will be replaced with the given text.

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
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed,
    ephemeral: bool = True,
    **kwargs,
):
    """Respond to an interaction or send an embed to a target.

    If the interaction has already been responded to,
    the message will be sent as a followup.

    Parameters
    ----------
    target:
        The application context or the interaction to send the message to.
    embed:
        The embed to send.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    if isinstance(target, discord.ApplicationContext) or isinstance(target, discord.Interaction):
        if not target.response.is_done():
            await target.response.send_message(embed=embed, ephemeral=ephemeral, **kwargs)
        else:
            await target.followup.send(embed=embed, ephemeral=ephemeral, **kwargs)
    else:
        await target.send(embed=embed, **kwargs)


async def _process_message(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed,
    txt: str,
    title: str | None,
    ephemeral: bool,
    **kwargs,
):
    """Adds embed attributes to the embed before sending it.

    Parameters
    ----------
    target:
        The target to send the message to.
    txt:
        The text to send.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral.
    """
    embed.description = txt
    if title is not None:
        embed.title = title

    await _send_embed(target, embed, ephemeral, **kwargs)


@copy_kwargs(discord.InteractionResponse.send_message)
async def error(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    *,
    title: str | None = None,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an error message. By default, this is a red embed.

    Parameters
    ----------
    target:
        The target to send the message to.
    txt:
        The text for the embed description.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("error_embed")
    await _process_message(target, embed.copy(), txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def success(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    *,
    title: str | None = None,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a success message. By default, this is a green embed.

    Parameters
    ----------
    target:
        The target to send the message to.
    txt:
        The text for the embed description.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("success_embed")
    await _process_message(target, embed.copy(), txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def warn(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    *,
    title: str | None = None,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a warning message. By default, this is a golden embed.

    Parameters
    ----------
    target:
        The target to send the message to.
    txt:
        The text for the embed description.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("warn_embed")
    await _process_message(target, embed.copy(), txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def info(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    *,
    title: str | None = None,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an info message. By default, this is a blue embed.

    Parameters
    ----------
    target:
        The target to send the message to.
    txt:
        The text to send.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("info_embed")
    await _process_message(target, embed.copy(), txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def send(
    template: str,
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    *,
    title: str | None = None,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a custom embed template. This needs to be set up with :func:`set_embed_templates`.

    Parameters
    ----------
    template:
        The name of the template that was used in :func:`set_embed_templates`.
    target:
        The target to send the message to.
    txt:
        The text to send.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed(template)
    await _process_message(target, embed.copy(), txt, title, ephemeral, **kwargs)
