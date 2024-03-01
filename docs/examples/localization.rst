Localization
=======================
You can localize commands and strings with EzCord.
More information can be found in the :doc:`Localization Documentation </ezcord/i18n>`.
This is currently only available for Pycord.

- You can localize **commands** by passing a dictionary of all commands and groups to
  :meth:`~ezcord.bot.Bot.localize_commands`
- Other strings can be localized with the :class:`~ezcord.i18n.I18N` class

.. warning::
   The following cases can't get the current locale automatically. You can use the ``use_locale``
   parameter to pass an object to extract the locale automatically.

   - **followup.send** - Use ``interaction.respond`` instead (or pass the interaction manually using the ``use_locale`` argument
   - **followup.edit_message** - Pass the interaction manually using the ``use_locale`` argument
   - **DMs** - Pass a localizable object manually using the ``use_locale`` argument

Localize Commands
-----------------
In this example, the commands are stored in ``commands.yaml``. Create a key for every command
and group that you want to localize. The key is the name of the command or group.

.. literalinclude:: ../../examples/localization/commands.yaml
   :language: yaml
   :caption: commands.yaml

.. literalinclude:: ../../examples/localization/localization.py
   :language: python
   :caption: main.py

Localize Strings
----------------
Create a language file (in this case ``en.yaml``) with the following structure:

- Create a key for every file name
- Inside the file name keys, you can create a key for every method name where you need to localize strings.
  You can use the class name as well, that's useful for Views or Modals.

Variables can be defined in the language file with curly braces.

.. note::
   The following **variable types** are available. You can find examples for all types below.

   - **General:** Can be used anywhere in the language file and in the code
   - **General, but inside a file name key:** Can be used within this file name key by placing a dot before the variable
   - **Method specific:** These variables are specified in the code and will be replaced with the given value

If general values are used within the language file, they are replaced with their value when the language file is loaded.

.. literalinclude:: ../../examples/localization/en.yaml
   :language: yaml
   :caption: en.yaml

Usage Example
-------------
The language file keys can be used in multiple ways.

- You can use the :meth:`~ezcord.i18n.t` function to get a localized string
- You can use the :class:`~ezcord.i18n.TEmbed` class if you want to define the embed in the language file
- You can simply use the language file keys as message content
- You can even use language file keys directly in embeds, views and modals! Just make sure that
  the key is in the language file matches the current method or class name.

Variables can be passed directly to all send/edit methods like ``ctx.respond`` like in the example below.
You can also pass variables to :meth:`~ezcord.i18n.t` or :class:`~ezcord.i18n.TEmbed`.

.. literalinclude:: ../../examples/localization/example_cog.py
   :language: python
   :caption: example_cog.py
