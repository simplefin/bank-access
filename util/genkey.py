#!/usr/bin/env python
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import sys
import gnupg
from twisted.internet import task
from siloscript.storage import gnupgWrapper, MemoryStore
from twisted.python.procutils import which


def main(reactor, homedir):
    gpg = gnupg.GPG(homedir=homedir, binary=which('gpg')[0])
    store = gnupgWrapper(gpg, MemoryStore())
    return store.put('dockerbuild', 'silo', 'key', 'dummy')

task.react(main, [sys.argv[1]])
