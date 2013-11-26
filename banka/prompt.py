# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
"""
Utilities to be used within bank scripts for asking the parent process for
information.

@var prompt: A function for prompting over the channel 3 medium.
@var save: A function for saving over the channel 3 medium.
"""

__all__ = ['save', 'prompt', 'alias']

import os
import json

from zope.interface import implements

from banka.interface import IInfoSource


def writeTo3(question):  # pragma: no cover
    """
    Write a piece of data as JSON to file descriptor 3.
    """
    os.write(3, json.dumps(question) + '\n')


def readFromStdin():  # pragma: no cover
    """
    Read a line of JSON data from stdin.
    """
    return json.loads(raw_input())


class ParentInfoSource(object):
    """
    I get information from the parent process.
    """

    implements(IInfoSource)

    def __init__(self):
        self.writer = writeTo3
        self.reader = readFromStdin

    def prompt(self, key, prompt=None, ask_human=True):
        """
        Request a piece of data from the parent process.

        @param key: String key identifying information.
        @param prompt: Optional alternate prompt for piece of data.
        @param ask_human: C{True} means I may ask a human.  C{False} means
            I will not ask a human.

        @return: The value for the piece of requested data.
        """
        msg = {
            'action': 'prompt',
            'key': key,
        }
        if prompt:
            msg['prompt'] = prompt
        if not ask_human:
            msg['ask_human'] = False
        self.writer(msg)
        return self.reader()

    def save(self, key, value):
        """
        Request a piece of data be saved.
        """
        self.writer({
            'action': 'save',
            'key': key,
            'value': value,
        })

    def alias(self, account_id):
        """
        Get a secure alias for an account id.

        Note that this will not be consistent if there is no store
        storing the aliases.

        @param account_id: Account ID as from the bank.
        @type account_id: C{str}

        @return: an alias
        @rtype: C{str}
        """
        self.writer({
            'action': 'alias',
            'account_id': account_id,
        })
        return self.reader()

_prompter = ParentInfoSource()
prompt = _prompter.prompt
save = _prompter.save
alias = _prompter.alias
