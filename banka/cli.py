# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import sys
import getpass
from functools import partial

from banka.wrap3 import Wrap3Protocol, wrap3Prompt


def wrap3(args):
    """
    Spawn a process and reroute channel 3 to getpass calls.

    @param args: List of commandline arguments (the first one is an
        executable)
    """
    from twisted.internet.task import react
    return react(_wrap3, [args])


def _wrap3(reactor, args):
    prompter = partial(wrap3Prompt, getpass.getpass)
    proto = Wrap3Protocol(prompter, stdout=sys.stdout, stderr=sys.stderr)
    reactor.spawnProcess(proto, args[0], args=args, env=None, childFDs={
        0: 'w',
        1: 'r',
        2: 'r',
        3: 'r',
    })

    def cb(status):
        return

    def eb(status):
        sys.exit(status.value.exitCode)
    return proto.done.addCallbacks(cb, eb)
