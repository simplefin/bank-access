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
        """
        @param writer: A function that accepts a prompt dictionary and is
            responsible for transmitting a corresponding request to whoever
            should answer the prompt (e.g. the parent process).

        @param reader: A function of no arguments that is called immediately
            after writing a prompt if an answer is expected.
        """
        self.writer = writer
        self.reader = reader

    def prompt(self, key, ask_human=True):
        """
        Prompt for some information.

        @param key: String key name for this information.
        @param ask_human: Pass along to he who answers whether or not a human
            should be asked for the answer.
        """
        msg = {'key': key}
        if not ask_human:
            msg['ask_human'] = False
        self.writer(msg)
        return self.reader()


_prompter = _Prompter()
prompt = _prompter.prompt
