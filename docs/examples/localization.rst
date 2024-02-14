Localization
=======================
You can localize commands and strings with EzCord.
More information can be found in the :doc:`Localization Documentation </ezcord/i18n>`.

Command Localization
--------------------
You can localize commands by passing a dictionary of all commands and groups to
:meth:`~ezcord.bot.Bot.localize_commands`.

.. literalinclude:: ../../examples/localization/commands.py
   :language: python

String Localization
-------------------
.. literalinclude:: ../../examples/localization/example_en.yaml
   :language: yaml
   :caption: example_en.yaml

.. literalinclude:: ../../examples/localization/localization.py
   :language: python
   :caption: main.py

.. literalinclude:: ../../examples/localization/example_cog.py
   :language: python
   :caption: example_cog.py
