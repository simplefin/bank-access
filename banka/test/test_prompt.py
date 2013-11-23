# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import sys

from unittest import TestCase
from StringIO import StringIO
from mock import MagicMock

from banka.prompt import _Prompter, writeTo3, readFromStdin


class PrompterTest(TestCase):

    def test_default(self):
        """
        Prompter will use raw_input for reader and writeTo3 for writer.
        """
        p = _Prompter()
        self.assertEqual(p.reader, readFromStdin)
        self.assertEqual(p.writer, writeTo3)
        self.assertEqual(p.logstream, sys.stderr)

    def test_simple(self):
        """
        If a single argument is provided, then it is the key of the prompt,
        and will be written using the writer method.
        """
        writer = []
        reader = MagicMock(return_value='something')
        p = _Prompter(writer.append, reader)
        r = p.prompt('foo')
        self.assertEqual(writer, [{"key": "foo"}])
        reader.assert_called_once_with()
        self.assertEqual(r, 'something')

    def test_prompt_dontAskHuman(self):
        """
        If C{ask_human} is C{False}, then include that in the prompt.
        """
        writer = []
        reader = MagicMock(return_value='something')
        p = _Prompter(writer.append, reader)
        r = p.prompt('foo', ask_human=False)
        self.assertEqual(writer, [{'key': 'foo', 'ask_human': False}])
        reader.assert_called_once_with()
        self.assertEqual(r, 'something')

    def test_save(self):
        """
        You can request that data be saved, and expect no answer.
        """
        writer = []
        reader = MagicMock(return_value='something')
        p = _Prompter(writer.append, reader)
        r = p.save('foo', 'some value')
        self.assertEqual(writer, [{
            'key': 'foo',
            'action': 'save',
            'value': 'some value',
        }])
        self.assertEqual(reader.call_count, 0, "Should not have asked for "
                         "an answer back")
        self.assertEqual(r, None, "Should get None back")

    def test_log(self):
        """
        You can log things to the logstream.
        """
        logstream = StringIO()
        p = _Prompter(None, None, logstream)
        p.log('foo')
        self.assertEqual(logstream.getvalue(), 'foo\n')

        p.log('foo', system='something')
        self.assertEqual(logstream.getvalue(), '[something] foo bar\n')
