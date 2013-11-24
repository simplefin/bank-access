# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import sys
import os
import getpass
import json
import yaml
from functools import partial

from twisted.internet import defer
from twisted.python import usage

from banka.inst import directory
from banka.wrap3 import Wrap3Protocol, wrap3Prompt, answererReceiver
from banka.wrap3 import StorebackedAnswerer, HumanbackedAnswerer, Runner
from banka.datastore import PasswordStore


#------------------------------------------------------------------------------
# run
#------------------------------------------------------------------------------
class RunOptions(usage.Options):

    synopsis = 'cmd [arg ...]'

    optFlags = [
        ('non-package', 'N', "Run a script from the given path rather than "
                             "relative to the banka/inst directory."),
    ]

    optParameters = [
        ('store', 's', None,
            "Database URI to store things in.  "
            "If provided, "
            "you will be prompted for a password "
            "(which will be used to encrypt stored data)."),
    ]

    def parseArgs(self, *args):
        self['args'] = args

    def doCommand(self):
        """
        Spawn a process and reroute channel 3 to getpass calls.

        @param args: List of commandline arguments (the first one is an
            executable)
        """
        from twisted.internet.task import react
        return react(self._doCommand, [self['args']])

    def _doCommand(self, reactor, args):
        if self['store']:
            return self._runWithStore(reactor, args)
        else:
            return self._runWithoutStore(reactor, args)

    @defer.inlineCallbacks
    def _runWithStore(self, reactor, args):
        from norm import makePool
        from banka.sql import sqlite_patcher, SQLDataStore
        password = getpass.getpass('Data encryption password? ')
        pool = yield makePool(self['store'])
        yield sqlite_patcher.upgrade(pool)
        store = SQLDataStore(pool)
        enc_store = PasswordStore(store, password)

        # XXX put this elsewhere
        def asker(x):
            value = getpass.getpass(x)
            return value
        answerer = StorebackedAnswerer(enc_store, asker)
        ch3_receiver = partial(answererReceiver, answerer.doAction)
        r = yield self._run(reactor, args, ch3_receiver)
        defer.returnValue(r)

    def _runWithoutStore(self, reactor, args):
        ch3_receiver = partial(wrap3Prompt, getpass.getpass)
        return self._run(reactor, args, ch3_receiver)

    def _run(self, reactor, args, ch3_receiver):
        script = args[0]
        rest = args[1:]
        if not self['non-package']:
            # relative to banka/inst
            script = os.path.join(directory.fp.path, script)
        args = [script] + list(rest)
        proto = Wrap3Protocol(ch3_receiver,
                              stdout=sys.stdout, stderr=sys.stderr)
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


#------------------------------------------------------------------------------
# list
#------------------------------------------------------------------------------
class ListOptions(usage.Options):

    optFlags = [
        ('verbose', 'v', "Display name, domain and available scripts."),
        ('json', 'j', "Print data out as JSON."),
        ('yaml', 'y', "Print data out as YAML."),
    ]

    def __init__(self):
        usage.Options.__init__(self)
        self['names'] = []

    def opt_include(self, arg):
        """
        Only include this name (may be specified multiple times).
        """
        self['names'].append(arg)
    opt_i = opt_include

    def doCommand(self):
        names = directory.names()
        if self['names']:
            names = self['names']
        if self['json'] or self['yaml']:
            data = {}
            for name in names:
                data[name] = directory.details(name)
            if self['json']:
                print json.dumps(data, indent=2)
            else:
                print yaml.dump(data)
        elif self['verbose']:
            for name in names:
                details = directory.details(name)
                print '%s scripts: %s domain: %s name: %s' % (
                    name,
                    ','.join(sorted(details['scripts'])),
                    details['info']['domain'],
                    details['info']['name'],
                )
        else:
            print '\n'.join(names)


#------------------------------------------------------------------------------
# base
#------------------------------------------------------------------------------
class Options(usage.Options):

    subCommands = [
        ('list', None, ListOptions, "List institutions"),
        ('run', None, RunOptions, 'Run a process that prompts for sensitive '
                                  'information on fd 3.')
    ]


def main():
    options = Options()
    options.parseOptions()
    so = options.subOptions
    so.doCommand()
