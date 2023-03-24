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

from typing import Union

import discord
from discord import Embed, Color


async def _send_embed(
        ctx: Union[discord.ApplicationContext, discord.Interaction, discord.TextChannel, discord.Thread],
        embed: discord.Embed,
        view: discord.ui.View = None,
        ephemeral: bool = True
):
    if isinstance(ctx, discord.TextChannel) or isinstance(ctx, discord.Thread):
        if view is None:
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, view=view)

    elif isinstance(ctx, discord.ApplicationContext) or isinstance(ctx, discord.Interaction):
        if view is None:
            try:
                await ctx.response.send_message(embed=embed, ephemeral=ephemeral)
            except discord.InteractionResponded:
                await ctx.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            try:
                await ctx.response.send_message(embed=embed, ephemeral=ephemeral, view=view)
            except discord.InteractionResponded:
                await ctx.followup.send(embed=embed, ephemeral=ephemeral, view=view)

    else:
        raise TypeError("The context must be a channel, thread, or interaction.")


async def error(
        ctx: Union[discord.ApplicationContext, discord.Interaction, discord.TextChannel, discord.Thread],
        txt: str,
        view: discord.ui.View = None,
        ephemeral: bool = True
):
    """Send an error message.

    Parameters
    ----------
    ctx:
        The channel, thread, or interaction to send the message to.
    txt:
        The text to send.
    view:
        The view to send with the message.
    ephemeral:
        Whether the message should be ephemeral or not.

    """
    embed = Embed(
        description=txt,
        color=Color.red()
    )
    await _send_embed(ctx, embed, view, ephemeral)


async def success(
        ctx: Union[discord.ApplicationContext, discord.Interaction, discord.TextChannel, discord.Thread],
        txt: str,
        view: discord.ui.View = None,
        ephemeral: bool = True
):
    """Send a success message.

    Parameters
    ----------
    ctx:
        The channel, thread, or interaction to send the message to.
    txt:
        The text to send.
    view:
        The view to send with the message.
    ephemeral:
        Whether the message should be ephemeral or not.

    """
    embed = Embed(
        description=txt,
        color=Color.green()
    )
    await _send_embed(ctx, embed, view, ephemeral)
