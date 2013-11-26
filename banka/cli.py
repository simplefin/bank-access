# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import sys
import getpass
import json
import yaml

from twisted.internet import defer
from twisted.python import usage

from banka.inst import directory
from banka.wrap3 import StorebackedAnswerer, HumanbackedAnswerer, Runner
from banka.datastore import PasswordStore


#------------------------------------------------------------------------------
# run
#------------------------------------------------------------------------------
class RunOptions(usage.Options):

    synopsis = 'cmd [arg ...]'

    optFlags = [
        ('non-package', 'N', "Run a script from the given path rather than "
                             "one that comes with the banka package"),
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

    @defer.inlineCallbacks
    def _doCommand(self, reactor, args):
        answerer = yield self._getAnswerer()
        runner = Runner(answerer)

        def cb(status):
            return

        def eb(status):
            sys.exit(status.value.exitCode)

        d = runner.run(reactor, args)
        d.addCallbacks(cb, eb)
        yield d

    @defer.inlineCallbacks
    def _getAnswerer(self):
        # XXX put this elsewhere
        def asker(x):
            return getpass.getpass(x + '? ')

        answerer = None
        if self['store']:
            store = yield self._getStore()
            answerer = StorebackedAnswerer(store, asker)
        else:
            answerer = HumanbackedAnswerer(asker)
        defer.returnValue(answerer)

    @defer.inlineCallbacks
    def _getStore(self):
        from norm import makePool
        from banka.sql import sqlite_patcher, SQLDataStore
        password = getpass.getpass('Data encryption password? ')
        pool = yield makePool(self['store'])
        yield sqlite_patcher.upgrade(pool)
        store = SQLDataStore(pool)
        enc_store = PasswordStore(store, password)
        defer.returnValue(enc_store)


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
        ('run', None, RunOptions, 'Run a bank script')
    ]


def main():
    options = Options()
    options.parseOptions()
    so = options.subOptions
    so.doCommand()
