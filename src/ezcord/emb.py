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

from .internal.embed_templates import load_embed, save_embeds


def override_embeds(
    *,
    error_embed: discord.Embed | None = None,
    success_embed: discord.Embed | None = None,
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
    **kwargs:
        Additional embed templates.

    Example
    -------
    .. code-block:: python

        from ezcord import emb

        embed = discord.Embed(
            title="Error",
            color=discord.Color.orange()
        )
        emb.override_embeds(error_embed=embed)
    """
    save_embeds(error_embed=error_embed, success_embed=success_embed, **kwargs)


async def _send_embed(
    interaction: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed,
    ephemeral: bool = True,
    **kwargs,
):
    """Respond to an interaction or send an embed to a target.

    If the interaction has already been responded to,
    the message will be sent as a followup.

    Parameters
    ----------
    interaction:
        The application context or the interaction to send the message to.
    embed:
        The embed to send.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    if isinstance(interaction, discord.ApplicationContext) or isinstance(
        interaction, discord.Interaction
    ):
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral, **kwargs)
        else:
            await interaction.followup.send(embed=embed, ephemeral=ephemeral, **kwargs)
    else:
        await interaction.send(embed=embed, **kwargs)


async def error(
    ctx: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an error message. By default, this is a red embed.

    Parameters
    ----------
    ctx:
        The application context or the interaction to send the message to.
    txt:
        The text to send.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("error")
    embed.description = txt
    await _send_embed(ctx, embed, ephemeral, **kwargs)


async def success(
    ctx: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a success message. By default, this is a green embed.

    Parameters
    ----------
    ctx:
        The application context or the interaction to send the message to.
    txt:
        The text to send.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("success")
    embed.description = txt
    await _send_embed(ctx, embed, ephemeral, **kwargs)
