Localization
=======================
You can localize commands and strings with EzCord.
More information can be found in the :doc:`Localization Documentation </ezcord/i18n>`.
This is currently only available for Pycord.

.. warning::
   The following cases can't get the current locale automatically. You can use the ``use_locale``
   parameter to pass an object to extract the locale automatically.

   - **followup.send** - Use ``interaction.respond`` instead (or pass the interaction manually using the ``use_locale`` argument
   - **followup.edit_message** - Pass the interaction manually using the ``use_locale`` argument
   - **DMs** - Pass a localizable object manually using the ``use_locale`` argument

Localize Commands
-----------------
You can localize **commands** by passing a dictionary of all commands and groups to
:meth:`~ezcord.bot.Bot.localize_commands`.

In this example, the commands are stored in ``commands.yaml``. Create a key for every command
and group that you want to localize. The key is the name of the command or group.

.. literalinclude:: ../../examples/localization/commands.yaml
   :language: yaml
   :caption: commands.yaml

.. literalinclude:: ../../examples/localization/main.py
   :language: python
   :caption: main.py

Localize Strings
----------------
Strings can be localized by calling :class:`~ezcord.i18n.I18N` like in the example above.
Create a language file (in this case ``en.yaml``) and define all strings that you want to localize.

Variables can be defined with curly braces, as shown in the example below.

.. literalinclude:: ../../examples/localization/en.yaml
   :language: yaml
   :caption: en.yaml

Usage Example
-------------
The language file keys can be used almost everywhere throughout the Discord bot.
You can see some examples below.

.. literalinclude:: ../../examples/localization/example_cog.py
   :language: python
   :caption: example_cog.py
