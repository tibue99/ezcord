Contributing
=======================
I am always happy to receive contributions. Here is how to do it:

1. Fork this repository
2. Install dev dependencies and pre-commit hooks

::

   pip install -r requirements-dev.txt
   pre-commit install

3. Make your changes
4. Create a pull request

.. note::

   As EzCord supports multiple Discord Libraries, you can't import any of them directly.
   Instead, you should import them from the ``internal/dc`` module.

   .. code:: python

      from .internal.dc import discord, commands


Testing & Docs
--------------
Create an ``example_bot`` directory with a basic main file.
Import any features that you would like to test.

.. code:: python

    import ezcord

    bot = ezcord.Bot()
    bot.run()


You can build the documentation locally to check if it's working as expected.

.. code:: shell

   cd docs
   make html

Now you can open ``_build/html/index.html`` in your browser.


Other Resources
---------------
Feel free to create an `issue or feature request <https://github.com/tibue99/ezcord/issues>`_ on GitHub.
