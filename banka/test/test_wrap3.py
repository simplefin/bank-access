# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer
from StringIO import StringIO

from mock import MagicMock
from banka.wrap3 import Wrap3Protocol, wrap3Prompt


class Wrap3ProtocolTest(TestCase):

    def test_channel3Received(self):
        """
        When a channel 3 line is received, it should call the function passed
        in to __init__ along with the protocol instance.
        """
        called = []
        proto = Wrap3Protocol(lambda *a: called.append(a))
        proto.childDataReceived(3, 'foo\n')
        self.assertEqual(called, [(proto, 'foo')])

    def test_channel3Line(self):
        """
        If data is received in pieces, wait until there's a line before calling
        the channel3 handler.
        """
        called = []
        proto = Wrap3Protocol(lambda *a: called.append(a))
        proto.childDataReceived(3, 'foo')
        proto.childDataReceived(2, 'channel 2')
        proto.childDataReceived(1, 'channel 1')
        proto.childDataReceived(3, 'bar\n')
        self.assertEqual(called, [(proto, 'foobar')])

    def test_stdout_err(self):
        """
        Standard out and standard error data should be written out to this
        process' stdout, stderr
        """
        stdout = StringIO()
        stderr = StringIO()
        proto = Wrap3Protocol(lambda *a: None, stdout=stdout, stderr=stderr)
        proto.childDataReceived(2, 'channel 2')
        proto.childDataReceived(1, 'channel 1')
        self.assertEqual(stdout.getvalue(), 'channel 1')
        self.assertEqual(stderr.getvalue(), 'channel 2')

    def test_default_stdout_stderr(self):
        """
        If no stdout, stderr are given, use StringIOs instances.
        """
        proto = Wrap3Protocol(None)
        self.assertTrue(isinstance(proto.stdout, StringIO))
        self.assertTrue(isinstance(proto.stderr, StringIO))


class wrap3PromptTest(TestCase):

    def test_basic(self):
        """
        wrap3Prompt should return a function that, when called with a proto
        and line, will call the prompt function then write the result
        to stdin of the proto
        """
        proto = MagicMock()
        proto.transport = MagicMock()

        prompts = []

        def getpass(prompt):
            prompts.append(prompt)
            return 'hey'
        wrap3Prompt(getpass, proto, 'a line of data')
        self.assertEqual(prompts, ['a line of data'], "Should call the prompt "
                         "function with the prompt received")
        proto.transport.write.assert_called_once_with('hey\n')

    def test_deferred(self):
        """
        If the getpass function returns a Deferred, that should be handled.
        """
        proto = MagicMock()
        proto.transport = MagicMock()

        prompts = []

        def getpass(prompt):
            prompts.append(prompt)
            return defer.succeed('hey')
        wrap3Prompt(getpass, proto, 'a line of data')
        self.assertEqual(prompts, ['a line of data'])
        proto.transport.write.assert_called_once_with('hey\n')
