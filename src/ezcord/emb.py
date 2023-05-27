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

import copy

import discord

from .internal import copy_kwargs, load_embed, save_embeds


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
    embed: discord.Embed | str,
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
    content = None
    if isinstance(embed, str):
        content = embed
        embed = None

    if isinstance(target, discord.ApplicationContext) or isinstance(target, discord.Interaction):
        if not target.response.is_done():
            await target.response.send_message(
                content=content, embed=embed, ephemeral=ephemeral, **kwargs
            )
        else:
            await target.followup.send(content=content, embed=embed, ephemeral=ephemeral, **kwargs)
    else:
        await target.send(content=content, embed=embed, **kwargs)


def _replace_values(s: str, interaction: discord.Interaction) -> str:
    user = interaction.user
    s = s.replace("{user}", f"{user}")
    s = s.replace("{username}", user.name)
    s = s.replace("{user_mention}", user.mention)
    s = s.replace("{user_id}", f"{user.id}")
    s = s.replace("{user_avatar}", user.display_avatar.url)

    if interaction.guild:
        s = s.replace("{servername}", interaction.guild.name)
    else:
        s = s.replace("{servername}", interaction.client.user.name)

    if interaction.guild and interaction.guild.icon:
        s = s.replace("{server_icon}", interaction.guild.icon.url)
    else:
        s = s.replace("{server_icon}", interaction.client.user.display_avatar.url)

    return s


def _loop_object(content: dict | str, interaction: discord.Interaction) -> dict | str:
    if isinstance(content, str):
        return _replace_values(content, interaction)

    for key, value in content.items():
        if isinstance(value, str):
            content[key] = _replace_values(value, interaction)
        elif isinstance(value, list):
            items = []
            for element in value:
                items.append(_loop_object(element, interaction))
            content[key] = items
        elif isinstance(value, dict):
            content[key] = _loop_object(value, interaction)

    return content


def _insert_info(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed | str,
):
    if not isinstance(target, discord.ApplicationContext) and not isinstance(
        target, discord.Interaction
    ):
        return embed

    interaction = target
    if isinstance(target, discord.ApplicationContext):
        interaction = target.interaction

    if isinstance(embed, discord.Embed):
        embed = embed.to_dict()
    embed_dic = _loop_object(embed, interaction)

    if isinstance(embed, dict):
        return discord.Embed.from_dict(embed_dic)

    return embed_dic


async def _process_message(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    embed: discord.Embed | str,
    txt: str | None,
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
    if isinstance(embed, discord.Embed):
        embed = copy.deepcopy(embed)
        if txt is not None:
            embed.description = txt
        if title is not None:
            embed.title = title
    elif isinstance(embed, str) and embed == "":
        embed = txt

    embed = _insert_info(target, embed)

    await _send_embed(target, embed, ephemeral, **kwargs)


@copy_kwargs(discord.InteractionResponse.send_message)
async def error(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
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
        The text for the embed description. If this is ``None``,
        you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("error_embed")
    await _process_message(target, embed, txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def success(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
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
        The text for the embed description. If this is ``None``,
        you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("success_embed")
    await _process_message(target, embed, txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def warn(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
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
        The text for the embed description. If this is ``None``,
        you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("warn_embed")
    await _process_message(target, embed, txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def info(
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
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
        The text for the embed description. If this is ``None``,
        you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed("info_embed")
    await _process_message(target, embed, txt, title, ephemeral, **kwargs)


@copy_kwargs(discord.abc.Messageable.send)
async def send(
    template: str,
    target: discord.ApplicationContext | discord.Interaction | discord.abc.Messageable,
    txt: str | None = None,
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
        The text for the embed description. If this is ``None``,
        you need to provide a non-empty ``Embed`` when using :func:`set_embed_templates`.
    title:
        The title of the embed. Defaults to ``None``.
    ephemeral:
        Whether the message should be ephemeral. Defaults to ``True``.
    """
    embed = load_embed(template)
    await _process_message(target, embed, txt, title, ephemeral, **kwargs)
