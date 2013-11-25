# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import sys
import os

from twisted.trial.unittest import TestCase
from twisted.internet import defer, error
from twisted.python.failure import Failure

from StringIO import StringIO

from mock import MagicMock, create_autospec

from banka.inst import directory
from banka.wrap3 import Wrap3Protocol, wrap3Prompt, StorebackedAnswerer
from banka.wrap3 import answererReceiver, HumanbackedAnswerer, Runner


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

    def test_save(self):
        """
        Saves should be ignored because there's nothing to save to.
        """
        proto = MagicMock()
        getpass = MagicMock()
        wrap3Prompt(getpass, proto, '{"key":"name","action":"save"}\n')
        self.assertEqual(getpass.call_count, 0, "Should not prompt for "
                         "save action")
        self.assertEqual(proto.transport.write.call_count, 0, "Should not "
                         "write anything back for save action")


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

    def test_save(self):
        """
        Calls to C{'save'} should not cause anything to be written to the
        transport.
        """
        proto = MagicMock()

        answerer = MagicMock(return_value=defer.succeed('foo'))

        answererReceiver(answerer, proto, '{"key":"name","action":"save"}\n')
        answerer.assert_called_once_with(key='name', action='save')
        self.assertEqual(proto.transport.write.call_count, 0, "Should not "
                         "write anything back on save")


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
    def test_doAction_login(self):
        """
        When asked for _login, prompt the human and save the value for later.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'_login': 'the login'}))
        result = yield dbp.doAction('_login')
        self.assertEqual(result, 'the login')
        self.assertEqual(dbp.login, 'the login')

        # shouldn't store the login
        self.assertFailure(store.get('the login', '_login'), KeyError)

    @defer.inlineCallbacks
    def test_doAction_login_prompt(self):
        """
        The prompt given to the ask_human function can be different than the
        key.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'Account number': '123'}))

        result = yield dbp.doAction('_login', prompt='Account number')
        self.assertEqual(result, '123')

    @defer.inlineCallbacks
    def test_doAction_prompt_unicode(self):
        """
        Unicode should be converted to strings.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            u'\N{SNOWMAN}prompt': u'\N{SNOWMAN}value'
        }))
        dbp.login = u'\N{SNOWMAN}login'
        yield dbp.doAction(u'\N{SNOWMAN}key', prompt=u'\N{SNOWMAN}prompt')
        result = yield store.get(u'\N{SNOWMAN}login'.encode('utf-8'),
                                 u'\N{SNOWMAN}key'.encode('utf-8'))
        self.assertEqual(result, u'\N{SNOWMAN}value'.encode('utf-8'))

    @defer.inlineCallbacks
    def test_doAction_fromHuman(self):
        """
        By default, the human is asked for every piece of data.  The data is
        then stored in the data store.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            '_login': 'foo',
            'password': 'the password',
        }))

        yield dbp.doAction('_login')
        password = yield dbp.doAction('password')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

        stored_password = yield store.get('foo', 'password')
        self.assertEqual(stored_password, 'the password', "Should have stored"
                         " the password in the store")

        self.assertEqual(dbp.login, 'foo', "Should not change the login")

    @defer.inlineCallbacks
    def test_doAction_fromHuman_prompt(self):
        """
        The prompt to the human can be overridden.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            'The password, please': 'the password',
        }))
        dbp.login = 'foo'
        password = yield dbp.doAction('password', 'The password, please')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

    @defer.inlineCallbacks
    def test_doAction_secondTime(self):
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
        result = yield dbp.doAction('somekey')
        self.assertEqual(result, 'real value', "Should get the value from the "
                         "store if present")

    @defer.inlineCallbacks
    def test_doAction_dontAskHuman(self):
        """
        If C{ask_human} is C{False} then don't ask the human.  Instead return
        None.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        result = yield dbp.doAction('some key', ask_human=False)
        self.assertEqual(result, None, "Not in store and not going to ask "
                         "the human")

    @defer.inlineCallbacks
    def test_doAction_save(self):
        """
        If action is C{'save'} then save the data in the store without any
        human interaction.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        yield dbp.doAction('key', action='save', value='some value')
        value = yield store.get('foo', 'key')
        self.assertEqual(value, 'some value', "Should save in store")

    @defer.inlineCallbacks
    def test_doAction_save_unicode(self):
        """
        Everything should be turned into bytes.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = u'\N{SNOWMAN}login'

        yield dbp.doAction(u'\N{SNOWMAN}key',
                           action='save',
                           value=u'\N{SNOWMAN}value')
        value = yield store.get(u'\N{SNOWMAN}login'.encode('utf-8'),
                                u'\N{SNOWMAN}key'.encode('utf-8'))
        self.assertEqual(value, u'\N{SNOWMAN}value'.encode('utf-8'),
                         "Should save in store as encoded utf-8")


class HumanbackedAnswererTest(TestCase):

    def human(self, answers):
        def f(prompt_str):
            return answers[prompt_str]
        return f

    @defer.inlineCallbacks
    def test_doAction_prompt(self):
        """
        A prompt will be sent to the ask_human function.
        """
        hba = HumanbackedAnswerer(self.human({'_login': 'foo'}))
        result = yield hba.doAction('_login')
        self.assertEqual(result, 'foo')

    @defer.inlineCallbacks
    def test_doAction_alternatePrompt(self):
        """
        If the C{'prompt'} keyword is given, use that for the prompt.
        """
        hba = HumanbackedAnswerer(self.human({'Username': 'foo'}))
        result = yield hba.doAction('_login', prompt='Username')
        self.assertEqual(result, 'foo')

    @defer.inlineCallbacks
    def test_doAction_unicode(self):
        """
        Results should be bytes, not unicode.
        """
        hba = HumanbackedAnswerer(self.human({'_login': u'\N{SNOWMAN}'}))
        result = yield hba.doAction('_login')
        self.assertEqual(result, u'\N{SNOWMAN}'.encode('utf-8'))
        self.assertEqual(type(result), str)

    @defer.inlineCallbacks
    def test_doAction_dontAskHuman(self):
        """
        If the human ought not be asked, then return None.
        """
        hba = HumanbackedAnswerer(self.human({'_login': 'foo'}))
        result = yield hba.doAction('_login', ask_human=False)
        self.assertEqual(result, None, "No human should have been asked")

    @defer.inlineCallbacks
    def test_doAction_save(self):
        """
        The save action is ignored and given a None response.
        """
        hba = HumanbackedAnswerer(self.human({}))
        result = yield hba.doAction('key', action='save', value='bar')
        self.assertEqual(result, None)


class RunnerTest(TestCase):

    timeout = 2

    def test_defaults(self):
        """
        Should have default stdout, stderr
        """
        r = Runner(None)
        self.assertEqual(r.stdout, sys.stdout)
        self.assertEqual(r.stderr, sys.stderr)

    def test_run(self):
        """
        Calling run should:

        1. Look up the full path of the script
        2. Create a protocol
        3. Spawn a process
        4. Return a deferred that callsback when the process is done.
        """
        reactor = MagicMock()
        answerer = MagicMock()
        proto = MagicMock()

        r = Runner(answerer)
        r.stdout = 'stdout'
        r.stderr = 'stderr'
        r.protocolFactory = create_autospec(r.protocolFactory,
                                            return_value=proto)
        r.ch3Maker = create_autospec(r.ch3Maker, return_value='ch3_receiver')
        r.scriptPath = create_autospec(r.scriptPath, return_value='abs/path')

        self.assertEqual(r.answerer, answerer)

        r.run(reactor, ('arg1', 'arg2', 'arg3'))
        r.ch3Maker.assert_called_once_with(answerer.doAction)
        r.scriptPath.assert_called_once_with('arg1')
        r.protocolFactory.assert_called_once_with('ch3_receiver',
                                                  stdout='stdout',
                                                  stderr='stderr')
        reactor.spawnProcess.assert_called_once_with(
            proto,
            'abs/path',
            args=['abs/path', 'arg2', 'arg3'],
            env=None,
            childFDs={0: 'w', 1: 'r', 2: 'r', 3: 'r'},
        )

    def test_scriptPath(self):
        """
        L{scriptPath} should return the given arg joined with the inst/
        abs path.
        """
        r = Runner(None)
        self.assertEqual(r.scriptPath('foo'),
                         os.path.join(directory.fp.path, 'foo'))

    def test_scriptPath_absPath(self):
        """
        If C{look_in_inst_package} is C{False},
        then scriptPath becomes an identity
        function.
        """
        r = Runner(None)
        r.look_in_inst_package = False
        self.assertEqual(r.scriptPath('foo'), 'foo')
