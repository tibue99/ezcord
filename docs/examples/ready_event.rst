Custom Ready Event
=======================

You can modify the default `on_ready` message by calling :meth:`~ezcord.bot.Bot.ready` in
your bot's ``on_ready`` event.

Optionally, EzCord can display an additional cog status table that adapts to the selected
ready event style.

Default Example
---------------

.. literalinclude:: ../../examples/custom_ready_event.py
   :language: python

Cog Status Table Example
------------------------

Here’s a small example showing the cog status table using the ``show_cogs_status`` option:

.. literalinclude:: ../../examples/cog_status_demo.py
   :language: python
