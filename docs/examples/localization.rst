Localization
=======================
You can localize commands and strings with EzCord.
More information can be found in the :doc:`Localization Documentation </ezcord/i18n>`.
This is currently only available for Pycord.

- You can localize **commands** by passing a dictionary of all commands and groups to
  :meth:`~ezcord.bot.Bot.localize_commands`
- Other strings can be localized with the :class:`~ezcord.i18n.I18N` class

In this example, the commands are stored in ``commands.yaml`` and the strings are stored in ``en.yaml``.

.. literalinclude:: ../../examples/localization/localization.py
   :language: python
   :caption: main.py

.. literalinclude:: ../../examples/localization/commands.yaml
   :language: yaml
   :caption: commands.yaml


Cog Example
-----------

.. literalinclude:: ../../examples/localization/example_cog.py
   :language: python
   :caption: example_cog.py

.. literalinclude:: ../../examples/localization/en.yaml
   :language: yaml
   :caption: en.yaml
