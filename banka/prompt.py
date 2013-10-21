# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
"""
@var prompt: A function for prompting over the channel 3 medium.
"""

import os
import json


def writeTo3(question):  # pragma: no cover
    os.write(3, json.dumps(question) + '\n')


def readFromStdin():  # pragma: no cover
    return json.loads(raw_input())


class _Prompter(object):
    """
    """

    def __init__(self, writer=writeTo3, reader=readFromStdin):
        self.writer = writer
        self.reader = reader

    def prompt(self, question):
        self.writer(question)
        return self.reader()


_prompter = _Prompter()
prompt = _prompter.prompt
