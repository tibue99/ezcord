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

   - Modify the English language file: ``ez_en.json``.
   - Create a new language file, ``ez_[language].json``.

   For example, if you want to create a French language file, the file name could be ``ez_fr.json``.

2. Copy the contents of the :ref:`language` into your new file and modify it.
3. Pass the language string into :meth:`~ezcord.bot.Bot` to set your language.

.. code-block:: python

   bot = ezcord.Bot(language="fr")  # French (loaded from ez_fr.json)


.. _language:

Language file
-------------

.. literalinclude:: ../../src/ezcord/internal/language/en.json
   :language: python
   :caption: The language file for English.
