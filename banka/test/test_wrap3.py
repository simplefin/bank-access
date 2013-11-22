# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer, error
from twisted.python.failure import Failure

from StringIO import StringIO

from mock import MagicMock
from banka.wrap3 import Wrap3Protocol, wrap3Prompt, DataBackedPrompter


class Wrap3ProtocolTest(TestCase):

    def test_channel3Received(self):
        """
        When a channel 3 line is received, it should call the function passed
        in to __init__ along with the protocol instance.
        """
        called = []
        proto = Wrap3Protocol(lambda *a: called.append(a))
        proto.childDataReceived(3, 'foo\n')
        self.assertEqual(called, [(proto, 'foo\n')])

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
        self.assertEqual(called, [(proto, 'foobar\n')])

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

    def test_done(self):
        """
        A done Deferred should be called back when the process is done.
        """
        proto = Wrap3Protocol(None)
        err = error.ProcessDone(0)
        proto.processEnded(Failure(err))
        self.assertEqual(self.successResultOf(proto.done), err)

    def test_doneError(self):
        """
        A done Deferred should be errbacked if a process exits with an error.
        """
        proto = Wrap3Protocol(None)
        err = Failure(error.ProcessTerminated(12))
        proto.processEnded(err)
        self.assertEqual(self.failureResultOf(proto.done), err)


class wrap3PromptTest(TestCase):

    def test_basic(self):
        """
        wrap3Prompt
        """
        proto = MagicMock()
        proto.transport = MagicMock()

        prompts = []

        def getpass(prompt):
            prompts.append(prompt)
            return 'hey'
        wrap3Prompt(getpass, proto, '{"key":"name"}\n')

        self.assertEqual(prompts, ['name? '], "Should call the prompt "
                         "function with the key received")
        proto.transport.write.assert_called_once_with('"hey"\n')

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
        wrap3Prompt(getpass, proto, '{"key":"name"}\n')
        self.assertEqual(prompts, ['name? '])
        proto.transport.write.assert_called_once_with('"hey"\n')


class DataBackedPrompterTest(TestCase):

    def test_init(self):
        """
        The L{DataBackedPrompter} should have a store and a human-prompting
        function.
        """
        dbp = DataBackedPrompter('store', 'prompt')
        self.assertEqual(dbp.store, 'store')
        self.assertEqual(dbp.ask_human, 'prompt')
