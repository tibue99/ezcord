Custom Ready Event
=======================

You can modify the default `on_ready` message by calling :meth:`~ezcord.bot.Bot.ready` in
your bot's ``on_ready`` event.

Optionally, EzCord can display an additional cog status table that automatically adapts to
the selected ready event style by using :attr:`~ezcord.CogLog.table` in
:meth:`~ezcord.bot.Bot.load_cogs`.

Default Example
---------------

.. literalinclude:: ../../examples/custom_ready_event.py
   :language: python

Cog Status Table Example
------------------------

The cog status table matches the style of your ready event. Here's an example using
:attr:`~ezcord.ReadyEvent.table_bold`:

.. literalinclude:: ../../examples/cog_status_demo.py
   :language: python

The table automatically adapts to the selected ready event style.
