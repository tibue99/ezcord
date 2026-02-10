Custom Ready Event
=======================

You can modify the default `on_ready` message by calling :meth:`~ezcord.bot.Bot.ready` in
your bot's ``on_ready`` event.

Optionally, EzCord can display a cog status table during cog loading by using
:attr:`~ezcord.CogLog.table` in :meth:`~ezcord.bot.Bot.load_cogs`.

Default Example
---------------

.. literalinclude:: ../../examples/custom_ready_event.py
   :language: python

Cog Status Table Example
------------------------

When loading cogs with :attr:`~ezcord.CogLog.table`, a status table is displayed showing
all loaded cogs:

.. literalinclude:: ../../examples/cog_status_demo.py
   :language: python
