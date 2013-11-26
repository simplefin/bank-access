# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import sys
import os
import json

from twisted.trial.unittest import TestCase
from twisted.internet import defer, error
from twisted.python.failure import Failure

from zope.interface.verify import verifyObject

from StringIO import StringIO

from mock import MagicMock, create_autospec

from banka.interface import IInfoSource
from banka.inst import directory
from banka.wrap3 import Wrap3Protocol, StorebackedAnswerer
from banka.wrap3 import answerProtocol, HumanbackedAnswerer, Runner


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


class answerProtocolTest(TestCase):

    def test_prompt_default(self):
        """
        Should call the C{prompt} method on the info source by default,
        then write the response as JSON to the protocol's transport.
        """
        proto = MagicMock()

        info_source = MagicMock()
        info_source.prompt.return_value = defer.succeed('foo')

        answerProtocol(info_source, proto, '{"key":"name"}\n')
        info_source.prompt.assert_called_once_with(key='name')
        proto.transport.write.assert_called_once_with('"foo"\n')

    def test_save(self):
        """
        Calls to C{'save'} should not cause anything to be written to the
        transport.
        """
        proto = MagicMock()

        info_source = MagicMock()
        info_source.save.return_value = defer.succeed('foo')

        answerProtocol(info_source, proto, json.dumps({
            "key": "name",
            "action": "save",
            "value": "foo",
        }))
        info_source.save.assert_called_once_with(key='name', value='foo')
        self.assertEqual(proto.transport.write.call_count, 0, "Should not "
                         "write anything back on save")

    def test_alias(self):
        """
        Should call alias function and write to transport the answer.
        """
        proto = MagicMock()

        info_source = MagicMock()
        info_source.alias.return_value = defer.succeed('foo')

        answerProtocol(info_source, proto, json.dumps({
            'action': 'alias',
            'account_id': 'foo'
        }))
        info_source.alias.assert_called_once_with(account_id='foo')
        proto.transport.write.assert_called_once_with('"foo"\n')

    def test_unknown(self):
        """
        Only commands that are part of the L{IInfoSource} interface can be
        called.  If an unknown command is encountered, raise L{TypeError}.
        """
        proto = MagicMock()

        info_source = MagicMock(return_value=defer.succeed('foo'))

        self.assertRaises(TypeError, answerProtocol, info_source, proto,
                          json.dumps({"action": "foo"}))
        self.assertEqual(info_source.foo.call_count, 0,
                         "Should not call foo")

        # XXX is this wise?
        self.assertEqual(proto.transport.write.call_count, 0, "Should not "
                         "write anything back on the transport")


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

    def test_IInfoSource(self):
        dbp = StorebackedAnswerer('store', 'prompt')
        verifyObject(IInfoSource, dbp)

    def test_init(self):
        """
        The L{StorebackedAnswerer} should have a store and a human-prompting
        function.
        """
        dbp = StorebackedAnswerer('store', 'prompt')
        self.assertEqual(dbp.store, 'store')
        self.assertEqual(dbp.ask_human, 'prompt')

    @defer.inlineCallbacks
    def test_prompt_login(self):
        """
        When asked for _login, prompt the human and save the value for later.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'_login': 'the login'}))
        result = yield dbp.prompt('_login')
        self.assertEqual(result, 'the login')
        self.assertEqual(dbp.login, 'the login')

        # shouldn't store the login
        self.assertFailure(store.get('the login', '_login'), KeyError)

    @defer.inlineCallbacks
    def test_prompt_login_prompt(self):
        """
        The prompt given to the ask_human function can be different than the
        key.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({'Account number': '123'}))

        result = yield dbp.prompt('_login', prompt='Account number')
        self.assertEqual(result, '123')

    @defer.inlineCallbacks
    def test_prompt_unicode(self):
        """
        Unicode should be converted to strings.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            u'\N{SNOWMAN}prompt': u'\N{SNOWMAN}value'
        }))
        dbp.login = u'\N{SNOWMAN}login'
        yield dbp.prompt(u'\N{SNOWMAN}key', prompt=u'\N{SNOWMAN}prompt')
        result = yield store.get(u'\N{SNOWMAN}login'.encode('utf-8'),
                                 u'\N{SNOWMAN}key'.encode('utf-8'))
        self.assertEqual(result, u'\N{SNOWMAN}value'.encode('utf-8'))

    @defer.inlineCallbacks
    def test_prompt_fromHuman(self):
        """
        By default, the human is asked for every piece of data.  The data is
        then stored in the data store.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            '_login': 'foo',
            'password': 'the password',
        }))

        yield dbp.prompt('_login')
        password = yield dbp.prompt('password')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

        stored_password = yield store.get('foo', 'password')
        self.assertEqual(stored_password, 'the password', "Should have stored"
                         " the password in the store")

        self.assertEqual(dbp.login, 'foo', "Should not change the login")

    @defer.inlineCallbacks
    def test_prompt_fromHuman_prompt(self):
        """
        The prompt to the human can be overridden.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({
            'The password, please': 'the password',
        }))
        dbp.login = 'foo'
        password = yield dbp.prompt('password', 'The password, please')
        self.assertEqual(password, 'the password', "Should have asked the "
                         "human for the password")

    @defer.inlineCallbacks
    def test_prompt_secondTime(self):
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
        result = yield dbp.prompt('somekey')
        self.assertEqual(result, 'real value', "Should get the value from the "
                         "store if present")

    @defer.inlineCallbacks
    def test_prompt_dontAskHuman(self):
        """
        If C{ask_human} is C{False} then don't ask the human.  Instead return
        None.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        result = yield dbp.prompt('some key', ask_human=False)
        self.assertEqual(result, None, "Not in store and not going to ask "
                         "the human")

    @defer.inlineCallbacks
    def test_save(self):
        """
        Save the data in the store without any human interaction.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        yield dbp.save('key', 'some value')
        value = yield store.get('foo', 'key')
        self.assertEqual(value, 'some value', "Should save in store")

    @defer.inlineCallbacks
    def test_save_unicode(self):
        """
        Everything should be turned into bytes.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = u'\N{SNOWMAN}login'

        yield dbp.save(u'\N{SNOWMAN}key', u'\N{SNOWMAN}value')
        value = yield store.get(u'\N{SNOWMAN}login'.encode('utf-8'),
                                u'\N{SNOWMAN}key'.encode('utf-8'))
        self.assertEqual(value, u'\N{SNOWMAN}value'.encode('utf-8'),
                         "Should save in store as encoded utf-8")

    @defer.inlineCallbacks
    def test_alias(self):
        """
        Should return the same alias for the same account id (because it's
        stored in the store)
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        alias1 = yield dbp.alias('account 1')
        alias2 = yield dbp.alias('account 1')
        self.assertEqual(alias1, alias2, "Should return the same alias for "
                         "the same account.")

    @defer.inlineCallbacks
    def test_alias_differentAccount(self):
        """
        Should return a different alias for different accounts.
        """
        store = yield self.getStore()
        dbp = StorebackedAnswerer(store, self.human({}))
        dbp.login = 'foo'

        alias1 = yield dbp.alias('account 1')
        alias2 = yield dbp.alias('account 2')
        self.assertNotEqual(alias1, alias2)

    @defer.inlineCallbacks
    def test_alias_differentLogin(self):
        """
        I'm torn, but I think the same account id for different logins should
        return the same alias.
        """
        store = yield self.getStore()
        d1 = StorebackedAnswerer(store, self.human({}))
        d1.login = 'foo'
        d2 = StorebackedAnswerer(store, self.human({}))
        d2.login = 'bar'

        alias2 = yield d1.alias('account 1')
        alias1 = yield d2.alias('account 1')
        self.assertEqual(alias1, alias2, "Account id alias should be the "
                         "same regardless of login")


class HumanbackedAnswererTest(TestCase):

    def human(self, answers):
        def f(prompt_str):
            return answers[prompt_str]
        return f

    def test_IInfoSource(self):
        hba = HumanbackedAnswerer('ask_human')
        verifyObject(IInfoSource, hba)

    @defer.inlineCallbacks
    def test_prompt(self):
        """
        A prompt will be sent to the ask_human function.
        """
        hba = HumanbackedAnswerer(self.human({'_login': 'foo'}))
        result = yield hba.prompt('_login')
        self.assertEqual(result, 'foo')

    @defer.inlineCallbacks
    def test_prompt_alternatePrompt(self):
        """
        If the C{'prompt'} keyword is given, use that for the prompt.
        """
        hba = HumanbackedAnswerer(self.human({'Username': 'foo'}))
        result = yield hba.prompt('_login', prompt='Username')
        self.assertEqual(result, 'foo')

    @defer.inlineCallbacks
    def test_prompt_unicode(self):
        """
        Results should be bytes, not unicode.
        """
        hba = HumanbackedAnswerer(self.human({'_login': u'\N{SNOWMAN}'}))
        result = yield hba.prompt('_login')
        self.assertEqual(result, u'\N{SNOWMAN}'.encode('utf-8'))
        self.assertEqual(type(result), str)

    @defer.inlineCallbacks
    def test_prompt_dontAskHuman(self):
        """
        If the human ought not be asked, then return None.
        """
        hba = HumanbackedAnswerer(self.human({'_login': 'foo'}))
        result = yield hba.prompt('_login', ask_human=False)
        self.assertEqual(result, None, "No human should have been asked")

    @defer.inlineCallbacks
    def test_save(self):
        """
        Saving is a nop for a HumanbackedAnswerer.
        """
        hba = HumanbackedAnswerer(self.human({}))
        result = yield hba.save('key', 'bar')
        self.assertEqual(result, None)

    @defer.inlineCallbacks
    def test_alias(self):
        """
        A human will not be asked to generate an alias at this point.  Instead,
        return a uuid.
        """
        hba = HumanbackedAnswerer(self.human({}))
        r1 = yield hba.alias('some account')
        r2 = yield hba.alias('some account')
        self.assertNotEqual(r1, r2, "Should return different alias for the "
                            "same account id")


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
        info_source = MagicMock()
        proto = MagicMock()

        r = Runner(info_source)
        r.stdout = 'stdout'
        r.stderr = 'stderr'
        r.protocolFactory = create_autospec(r.protocolFactory,
                                            return_value=proto)
        r.ch3Maker = create_autospec(r.ch3Maker, return_value='ch3_receiver')
        r.scriptPath = create_autospec(r.scriptPath, return_value='abs/path')

        self.assertEqual(r.info_source, info_source)

        r.run(reactor, ('arg1', 'arg2', 'arg3'))
        r.ch3Maker.assert_called_once_with(info_source)
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
