# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
"""
Utilities to be used within bank scripts for asking the parent process for
information.

@var prompt: A function for prompting over the channel 3 medium.
"""

import os
import json


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


class _Prompter(object):
    """
    """

    def __init__(self, writer=writeTo3, reader=readFromStdin):
        self.writer = writer
        self.reader = reader

    def prompt(self, key):
        """
        Prompt for some information.

        @param key: String key name for this information.
        """
        self.writer({
            'key': key,
        })
        return self.reader()


_prompter = _Prompter()
prompt = _prompter.prompt
