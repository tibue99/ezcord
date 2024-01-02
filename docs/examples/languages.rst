Language
=======================
You can modify the default language files and even create your own language files.

.. note::

   The following languages are available by default:

   - English (``en``)
   - German (``de``)


Modify language files
---------------------

1. Create a JSON file with the prefix ``ez_`` somewhere in your project.

   - If you want to modify the English language file: ``ez_en.json``.
   - If you want to create a new language file: ``ez_[language].json``.

   If you want to create a French language file, the file name could be ``ez_fr.json``.

2. Search the :ref:`language files <language>` and find keys you want to override.

   - Include any keys that you want to override in your JSON file.

3. Pass the language string into :meth:`~ezcord.bot.Bot` to set your language.

.. code-block:: python

   bot = ezcord.Bot(language="fr")  # French (loaded from ez_fr.json)

If your bot supports **multiple languages**, set ``language`` to ``auto`` to
automatically detect the language. You can set a fallback language with ``default_language``.

The fallback language is used when no language file is found for the detected language.

.. code-block:: python

   bot = ezcord.Bot(language="auto", default_language="en")


.. _language:

Language files
--------------

.. literalinclude:: ../../ezcord/internal/language/en.json
   :language: python
   :caption: The default language file for English.

.. literalinclude:: ../../ezcord/internal/language/de.json
   :language: python
   :caption: The default language file for German.
