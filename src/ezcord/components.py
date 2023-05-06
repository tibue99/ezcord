import discord


class EzView(discord.ui.View):
    """This class extends from :class:`discord.ui.View` and adds some functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_timeout(self) -> None:
        """Makes sure that items are only disabled if the message still has components.

        This is called when ``disable_on_timeout`` is set to ``True``.
        """
        if not self.disable_on_timeout:
            return

        if self._message:
            try:
                msg = await self._message.channel.fetch_message(self._message.id)
            except (discord.NotFound, discord.Forbidden):
                return

            if len(msg.components) > 0:
                self.disable_all_items()
                await self._message.edit(view=self)
