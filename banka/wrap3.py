# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from StringIO import StringIO

import sys
import os
import json
from uuid import uuid4

from functools import partial

from twisted.internet.protocol import ProcessProtocol
from twisted.internet import defer

from zope.interface import implements

from banka.interface import IInfoSource
from banka.inst import directory


class Wrap3Protocol(ProcessProtocol):
    """
    @ivar done: A Deferred which fires when this protocol is done.
    """

    def __init__(self, ch3_receiver, stdout=None, stderr=None):
        """
        @param ch3_receiver: A function that will be called with two arguments
            (this L{Wrap3Protocol} instance, the line) for every line on
            channel 3 that is received by this protocol.
        @param stdout: A file-like object to which stdout will be written.
        @param stderr: A file-like object to which stderr will be written.
        """
        self.ch3_receiver = ch3_receiver
        self._buffer = ''
        self.stdout = stdout or StringIO()
        self.stderr = stderr or StringIO()
        self.done = defer.Deferred()

    def childDataReceived(self, childFD, data):
        if childFD == 3:
            self._buffer += data
            while self._buffer.count('\n'):
                line, self._buffer = self._buffer.split('\n', 1)
                self.ch3_receiver(self, line+'\n')
        else:
            ProcessProtocol.childDataReceived(self, childFD, data)

    def outReceived(self, data):
        self.stdout.write(data)

    def errReceived(self, data):
        self.stderr.write(data)

    def processEnded(self, status):
        if status.value.exitCode == 0:
            self.done.callback(status.value)
        else:
            self.done.errback(status)


def answerProtocol(info_source, proto, line):
    """
    Using C{info_source} answer a question posed by C{proto}.

    @param info_source: A L{IInfoSource}-implementing thing.
    @param proto: A L{ProcessProtocol} (probably L{Wrap3Protocol})
    @param line: A line of data received by C{proto}.

    @raise TypeError: If C{line} contains a command that isn't acceptable.

    @return: C{None}
    """
    kwargs = json.loads(line)
    action = kwargs.pop('action', 'prompt')

    if not IInfoSource.get(action):
        raise TypeError('%r not a valid action' % (action,))

    function = getattr(info_source, action)
    d = defer.maybeDeferred(function, **kwargs)

    def _gotAnswer(answer, proto):
        if action not in ['save']:
            proto.transport.write(json.dumps(answer) + '\n')
    return d.addCallback(_gotAnswer, proto)


def _encode(str):
    if type(str) == unicode:
        return str.encode('utf-8')
    return str


class HumanbackedAnswerer(object):
    """
    I get all answers from a human.
    """

    implements(IInfoSource)

    def __init__(self, ask_human):
        self.ask_human = ask_human

    def prompt(self, key, prompt=None, ask_human=True):
        """
        Prompt the human for some bit of information.
        """
        prompt = prompt or key
        if not ask_human:
            return None
        return _encode(self.ask_human(prompt))

    def save(self, *args, **kwargs):
        """
        Ignore save requests (since we're not going to expect humans to write
        down long bytestrings).
        """
        return None

    def alias(self, account_id):
        """
        Return a random alias.

        Why random?  Because it's the most secure thing to do.  We don't want
        to reveal anything about the real account id from the alias.  If you
        want a consistent alias, use L{StorebackedAnswerer} instead.
        """
        return 'TRANSIENT-' + str(uuid4()).replace('-', '')


class StorebackedAnswerer(object):
    """
    I get my answers to the prompts either from a
    data store or else a human (if possible).

    @ivar login: The login string to be used when asked for C{'_login'}
    """

    implements(IInfoSource)

    login = None

    def __init__(self, store, ask_human):
        self.store = store
        self.ask_human = ask_human

    @defer.inlineCallbacks
    def prompt(self, key, prompt=None, ask_human=True):
        """
        Get a piece of data either from the store or from a human.

        @param key: name of data to get.
        @param prompt: String prompt to give to the human.  If not given,
            C{key} will be used instead.
        @param ask_human: If C{False} then don't ask the human for this data.
        """
        prompt = prompt or key
        key = _encode(key)
        login = _encode(self.login)

        # handle special _login case
        if key == '_login':
            value = self.ask_human(prompt)
            self.login = value
            defer.returnValue(value)

        value = None
        try:
            value = yield self.store.get(login, key)
        except KeyError:
            if ask_human:
                value = _encode(self.ask_human(prompt))
        if value is not None:
            yield self.store.put(login, key, value)
        defer.returnValue(value)

    def save(self, key, value):
        """
        Save some data in the store.
        """
        key = _encode(key)
        value = _encode(value)
        return self.store.put(_encode(self.login), key, value)

    @defer.inlineCallbacks
    def alias(self, account_id):
        """
        Get an alias for an account id.
        """
        try:
            alias = yield self.store.get('__alias', account_id)
        except KeyError:
            alias = ('%s%s' % (uuid4(), uuid4())).replace('-', '')
            yield self.store.put('__alias', account_id, alias)
        defer.returnValue(alias)


class Runner(object):
    """
    XXX
    """

    look_in_inst_package = True
    stdout = sys.stdout
    stderr = sys.stderr
    protocolFactory = Wrap3Protocol

    def __init__(self, info_source):
        """
        @param info_source: An L{IInfoSource}-implementing object.
        """
        self.info_source = info_source

    def ch3Maker(self, info_source):
        """
        XXX
        """
        # XXX this is only tested functionally
        return partial(answerProtocol, info_source)

    def scriptPath(self, arg0):
        """
        XXX
        """
        if self.look_in_inst_package:
            return os.path.join(directory.fp.path, arg0)
        else:
            return arg0

    def run(self, reactor, args):
        ch3_receiver = self.ch3Maker(self.info_source)
        path = self.scriptPath(args[0])
        proto = self.protocolFactory(ch3_receiver, stdout=self.stdout,
                                     stderr=self.stderr)
        reactor.spawnProcess(
            proto,
            path,
            args=[path]+list(args[1:]),
            env=None,
            childFDs={
                0: 'w',
                1: 'r',
                2: 'r',
                3: 'r',
            })
        return proto.done
