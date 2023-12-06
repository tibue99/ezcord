Getting Started
=======================
This page shows how to quickly get started with **EzCord**.

Installing
-----------
Python 3.9 or higher is required.
::

    pip install ezcord

You can also install the latest version from GitHub. Note that this version may be unstable.
::

    pip install git+https://github.com/tibue99/ezcord


First Steps
--------------
You should already have a basic understanding of **Discord.py** or **Pycord**.

1. Create a new bot in the `Discord Developer Portal <https://discord.com/developers/applications/>`_
2. Create a bot object using ``ezcord.Bot``


Example
--------------
A quick example of how EzCord works. You can find more examples :doc:`here </examples/examples>`.

.. literalinclude:: ../../examples/pycord.py
   :language: python
   :caption: Pycord

.. literalinclude:: ../../examples/dpy.py
   :language: python
   :caption: Discord.py
