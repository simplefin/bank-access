# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import sys
import getpass
import json
import yaml
from functools import partial

from twisted.python import usage

from banka.inst import directory
from banka.wrap3 import Wrap3Protocol, wrap3Prompt


#------------------------------------------------------------------------------
# run
#------------------------------------------------------------------------------
class RunOptions(usage.Options):

    synopsis = 'cmd [arg ...]'

    optFlags = [
        ('non-package', 'N', "Run a script from the given path rather than "
                             "relative to the banka/inst directory.")
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
