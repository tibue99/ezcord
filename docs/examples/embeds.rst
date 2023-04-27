Embed Templates
=======================
You can set **embed templates** that can be used to send error messages, warnings, and other messages.
If you don't set any custom templates, default templates will be used.

More information can be found in the :doc:`Embed Documentation </ezcord/embed>`.

.. literalinclude:: ../../examples/embed_templates.py
   :language: python

1. Pass a string to the :meth:`~ezcord.emb.error` method to send an error message.

   .. note::

       The string will be used as the description of the error embed.

2. The final embed will be sent as an interaction response or a normal message, depending on the target type.
