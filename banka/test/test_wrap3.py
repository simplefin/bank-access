# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from twisted.trial.unittest import TestCase
from twisted.internet import defer, error
from twisted.python.failure import Failure

from StringIO import StringIO

from mock import MagicMock
from banka.wrap3 import Wrap3Protocol, wrap3Prompt, StorebackedAnswerer
from banka.wrap3 import answererReceiver


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


class answererReceiverTest(TestCase):

    def test_basic(self):
        """
        Should call the first function with the JSON dictionary line as keyword
        arguments then write the JSON response to the protocols transport.
        """
        proto = MagicMock()

        answerer = MagicMock(return_value=defer.succeed('foo'))

        answererReceiver(answerer, proto, '{"key":"name"}\n')
        answerer.assert_called_once_with(key='name')
        proto.transport.write.assert_called_once_with('"foo"\n')


class StorebackedAnswererTest(TestCase):

    @defer.inlineCallbacks
    def getStore(self):
        """
        Get a useable store.
        """
        from norm import makePool
        from banka.sql import SQLDataStore, sqlite_patcher
        pool = yield makePool('sqlite:')
        yield sqlite_patcher.upgrade(pool)
        defer.returnValue(SQLDataStore(pool))

    def human(self, answers):
        def f(prompt_str):
            return answers[prompt_str]
        return f

    def test_init(self):
        """
        The L{StorebackedAnswerer} should have a store and a human-prompting
        function.
        """
        dbp = StorebackedAnswerer('store', 'prompt')
        self.assertEqual(dbp.store, 'store')
        self.assertEqual(dbp.ask_human, 'prompt')

    @defer.inlineCallbacks
    def test_getData_login(self):
        """
        When asked for _login, prompt the human and save the value for later.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'_login': 'the login'}))
        result = yield dbp.getData('_login')
        self.assertEqual(result, 'the login')
        self.assertEqual(dbp.login, 'the login')

        # shouldn't store the login
        self.assertFailure(store.get('the login', '_login'), KeyError)

    @defer.inlineCallbacks
    def test_getData_login_prompt(self):
        """
        The prompt given to the ask_human function can be different than the
        key.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'Account number': '123'}))

        result = yield dbp.getData('_login', prompt='Account number')
        self.assertEqual(result, '123')

    @defer.inlineCallbacks
    def test_getData_fromHuman(self):
        """
        By default, the human is asked for every piece of data.  The data is
        then stored in the data store.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            '_login': 'foo',
            'password': 'the password',
        }))

        yield dbp.getData('_login')
        password = yield dbp.getData('password')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

        stored_password = yield store.get('foo', 'password')
        self.assertEqual(stored_password, 'the password', "Should have stored"
                         " the password in the store")

        self.assertEqual(dbp.login, 'foo', "Should not change the login")

    @defer.inlineCallbacks
    def test_getData_fromHuman_prompt(self):
        """
        The prompt to the human can be overridden.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            'The password, please': 'the password',
        }))
        dbp.login = 'foo'
        password = yield dbp.getData('password', 'The password, please')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

    @defer.inlineCallbacks
    def test_getData_secondTime(self):
        """
        If the data is in the store, get it from the store and not the human.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            'somekey': 'fake value',
        }))
        dbp.login = 'foo'

        # load the store
        yield store.put('foo', 'somekey', 'real value')
        result = yield dbp.getData('somekey')
        self.assertEqual(result, 'real value', "Should get the value from the "
                         "store if present")

    @defer.inlineCallbacks
    def test_getData_dontAskHuman(self):
        """
        If C{ask_human} is C{False} then don't ask the human.  Instead return
        None.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        result = yield dbp.getData('some key', ask_human=False)
        self.assertEqual(result, None, "Not in store and not going to ask "
                         "the human")
