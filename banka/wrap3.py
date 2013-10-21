# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from StringIO import StringIO
from twisted.internet.protocol import ProcessProtocol
from twisted.internet import defer


class Wrap3Protocol(ProcessProtocol):

    def __init__(self, ch3_receiver, stdout=None, stderr=None):
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
                self.ch3_receiver(self, line)
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
        #self.done.callback(status.value)


def wrap3Prompt(getpass_fn, proto, prompt):
    """
    @param getpass_fn: A function that will be called with a prompt and is
        expected to return an answer.
    @param proto: A L{ProcessProtocol} instance whose stdin will receive the
        answer to this prompt.
    @param prompt: String prompt
    """
    d = defer.maybeDeferred(getpass_fn, prompt)

    def _gotAnswer(answer, proto):
        proto.transport.write(answer + '\n')

    d.addCallback(_gotAnswer, proto)
