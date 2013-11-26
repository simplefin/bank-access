# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from zope.interface import Interface


class IInfoSource(Interface):
    """
    An interface to be used to ask questions and store answers.
    """

    def prompt(key, prompt=None, ask_human=True):
        """
        Ask for a piece of data by key.

        @param key: Unique key describing the requested data.
        @type key: str

        @param prompt: Optional nice name to present to human when prompting.

        @param ask_human: C{True} means a human may be asked.  C{False} means
            a human must not be asked.

        @return: Answer to the prompt, either C{Deferred} or not.
        @rtype: C{str}
        """

    def save(key, value):
        """
        Save a piece of data for later

        Or at least pretend to.  The L{IInfoSource} is under no obligation to
        do anything with this data.

        @param key: Unique key describing the requested data.
        @type key: str

        @param value: Value to save.
        @type value: str

        @return: C{None}
        """
