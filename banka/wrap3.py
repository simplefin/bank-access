# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from StringIO import StringIO
import json
from twisted.internet.protocol import ProcessProtocol
from twisted.internet import defer


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


def wrap3Prompt(getpass_fn, proto, line):
    """
    @param getpass_fn: A function that will be called with a string prompt and
        is expected to return a string answer.
    @param proto: A L{ProcessProtocol} instance whose stdin will receive the
        answer to this prompt.
    @param line: Line of data containing some JSON.
    """
    data = json.loads(line)
    prompt = '%s? ' % (data['key'],)
    d = defer.maybeDeferred(getpass_fn, prompt)

    def _gotAnswer(answer, proto):
        proto.transport.write(json.dumps(answer) + '\n')

    d.addCallback(_gotAnswer, proto)


class StorebackedAnswerer(object):
    """
    My L{getData} function can be used as a C{ch3_receiver} in
    L{Wrap3Protocol} if it's wrapped in L{wrapAnswerer).

    I get my answers to the prompts either from a
    data store or else a human (if possible).

    @ivar login: The login string to be used when asked for C{'_login'}
    """

    login = None

    def __init__(self, store, ask_human):
        self.store = store
        self.ask_human = ask_human

    @defer.inlineCallbacks
    def getData(self, key, prompt=None, ask_human=True):
        """
        Get a piece of data either from the store or from a human.

        @param key: name of data to get.
        @param prompt: String prompt to give to the human.  If not given,
            C{key} will be used instead.
        @param ask_human: If C{False} then don't ask the human for this data.
        """
        prompt = prompt or key

        # handle special _login case
        if key == '_login':
            value = self.ask_human(prompt)
            self.login = value
            defer.returnValue(value)

        value = None
        try:
            value = yield self.store.get(self.login, key)
        except KeyError:
            if ask_human:
                value = self.ask_human(prompt)
        if value is not None:
            yield self.store.put(self.login, key, value)
        defer.returnValue(value)
