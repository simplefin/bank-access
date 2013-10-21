# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from unittest import TestCase
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

    def test_works(self):
        """
        A prompter will write prompts using writePrompt and read data using
        readAnswer.
        """
        writer = []
        reader = MagicMock(return_value='something')
        p = _Prompter(writer.append, reader)
        self.assertEqual(p.writer, writer.append)
        self.assertEqual(p.reader, reader)
        r = p.prompt('foo')
        self.assertEqual(writer, ['foo'])
        reader.assert_called_once_with()
        self.assertEqual(r, 'something')
