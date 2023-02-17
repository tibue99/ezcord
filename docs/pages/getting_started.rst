Getting Started
=======================
This page shows how to quickly get started with **EzCord**.

Installing
-----------
::

    pip install ezcord


First Steps
--------------
You should already have a basic understanding of how to use **Pycord**.
If you don't, you can find the documentation `here <https://docs.pycord.dev/>`_.

1. Create a new bot in the `Discord Developer Portal <https://discord.com/developers/applications/>`_
2. Create a bot object using ``ezcord.Bot``


Example
--------------
A quick example of how Ezcord works

.. code-block:: python3

    import ezcord
    import discord

    bot = ezcord.Bot(
        intents=discord.Intents.default()
    )

    if __name__ == "__main__":
        bot.load_cogs("cogs")  # Load all cogs in the "cogs" folder
        bot.run("TOKEN")
