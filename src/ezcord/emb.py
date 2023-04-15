"""Embed templates that can be used to send messages to users.
These functions will generate embeds and send them as an ephemeral message to the user.

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
from discord import Color, Embed


async def _send_embed(
    interaction: discord.ApplicationContext | discord.Interaction,
    embed: discord.Embed,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an embed to the user. If the interaction has already been responded to,
    the message will be sent as a followup.

    Parameters
    ----------
    interaction:
        The application context or the interaction to send the message to.
    embed:
        The embed to send.
    ephemeral:
        Whether the message should be ephemeral.
    """
    try:
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral, **kwargs)
    except discord.InteractionResponded:
        await interaction.followup.send(embed=embed, ephemeral=ephemeral, **kwargs)


async def error(
    ctx: discord.ApplicationContext | discord.Interaction,
    txt: str,
    ephemeral: bool = True,
    **kwargs,
):
    """Send an error message.

    Parameters
    ----------
    ctx:
        The application context or the interaction to send the message to.
    txt:
        The text to send.
    ephemeral:
        Whether the message should be ephemeral.
    """
    embed = Embed(description=txt, color=Color.red())
    await _send_embed(ctx, embed, ephemeral, **kwargs)


async def success(
    ctx: discord.ApplicationContext | discord.Interaction,
    txt: str,
    ephemeral: bool = True,
    **kwargs,
):
    """Send a success message.

    Parameters
    ----------
    ctx:
        The application context or the interaction to send the message to.
    txt:
        The text to send.
    ephemeral:
        Whether the message should be ephemeral.
    """
    embed = Embed(description=txt, color=Color.green())
    await _send_embed(ctx, embed, ephemeral, **kwargs)
