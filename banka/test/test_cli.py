# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet.protocol import ProcessProtocol
from twisted.internet import reactor, defer
from twisted.python.filepath import FilePath
from twisted.python import log

import sys
import os
import json
import yaml

from StringIO import StringIO

from norm import makePool

from banka.inst import directory
from banka.sql import SQLDataStore
from banka.datastore import PasswordStore


class StdinProtocol(ProcessProtocol):
    """
    @ivar done: A Deferred which fires when this protocol is done.
    """

    def __init__(self, responses):
        """
        @param responses: A list of responses to be given in order as stdout
            lines are received.
        """
        self.responses = responses
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.done = defer.Deferred()

    def outReceived(self, data):
        log.msg(repr(data), system='stdout')
        self.stdout.write(data)
        if self.responses and data.strip():
            r = self.responses.pop(0)
            log.msg(repr(r), system='stdin')
            self.transport.write(r)
            if not self.responses:
                self.transport.closeStdin()

    def errReceived(self, data):
        log.msg(repr(data), system='stderr')
        self.stderr.write(data)

    def processEnded(self, status):
        self.done.callback(status.value.exitCode)


class runTest(TestCase):

    timeout = 8

    @defer.inlineCallbacks
    def test_basicPackage(self):
        """
        Calling run will run scripts relative to the banka/inst directory
        by default
        """
        root = directory.fp

        temp = root.child('_temp')
        temp.makedirs()
        self.addCleanup(temp.remove)

        script = temp.child('foo')

        script.setContent(
            '#!%s\n'
            'from banka.prompt import prompt\n'
            'data = prompt("_login")\n'
            'print "got %%s" %% (data,)\n' % (sys.executable,))

        proto = runScript('../bin/banka', ['banka', 'run', '_temp/foo'],
                          ['hey\n'], usePTY=True)
        rc = yield proto.done
        self.assertEqual(rc, 0)

        self.assertIn('got hey', proto.stdout.getvalue())

    def test_basicNonPackage(self):
        """
        Calling run should spawn a process that listens on channel 3 for
        prompts and uses the tty to get answers.
        """
        script_file = FilePath(self.mktemp())
        script_file.setContent(
            '#!%s\n'
            'from banka.prompt import prompt\n'
            'data = prompt("_login")\n'
            'print "got %%s" %% (data,)\n' % (sys.executable,))

        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.abspath('..')
        env['COVERAGE_PROCESS_START'] = os.path.abspath('../.coveragerc')
        proto = StdinProtocol(['joe\n'])
        reactor.spawnProcess(proto, '../bin/banka',
                             ['banka', 'run', '--non-package',
                              script_file.path],
                             env=env, usePTY=True)

        def check(result):
            stdout_lines = proto.stdout.getvalue().split('\r\n')
            self.assertIn('got joe', stdout_lines)
        return proto.done.addCallback(check)

    @defer.inlineCallbacks
    def test_store(self):
        """
        You can specify an SQL database URI to store things in.  If specified,
        it will ask for a password to encrypt things.
        """
        script1 = FilePath(self.mktemp())
        script1.setContent(
            '#!%s\n'
            'from banka.prompt import prompt, save\n'
            'login = prompt("_login")\n'
            '_ = save("foo", "value")\n'
            'foo = prompt("foo")\n'
            'print "got %%r %%r" %% (login, foo)\n' % (sys.executable,))

        sqlite_path = self.mktemp()
        sqlite_uri = 'sqlite:' + sqlite_path

        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.abspath('..')
        env['COVERAGE_PROCESS_START'] = os.path.abspath('../.coveragerc')
        proto = StdinProtocol(['password\n', 'joe\n'])
        reactor.spawnProcess(
            proto,
            '../bin/banka',
            [
                'banka', 'run',
                '--store', sqlite_uri,
                '--non-package', script1.path,
            ],
            env=env, usePTY=True
        )

        yield proto.done

        stdout_lines = proto.stdout.getvalue().split('\r\n')
        self.assertIn("got 'joe' 'value'", stdout_lines)

        # decrypt some stuff with the password
        pool = yield makePool(sqlite_uri)
        sql_store = SQLDataStore(pool)
        store = PasswordStore(sql_store, 'password')

        foo = yield store.get('joe', 'foo')
        self.assertEqual(foo, 'value', "Should have stored the encrypted data")

    def test_error(self):
        """
        If the script exits with exit code 10, it should exit the wrapper with
        exit code 10.
        """
        script_file = FilePath(self.mktemp())
        script_file.setContent(
            '#!%s\n'
            'import sys\n'
            'sys.exit(10)\n' % (sys.executable,))

        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.abspath('..')
        env['COVERAGE_PROCESS_START'] = os.path.abspath('../.coveragerc')
        proto = StdinProtocol([])
        reactor.spawnProcess(proto, '../bin/banka',
                             ['banka', 'run', '--non-package',
                              script_file.path],
                             env=env)

        def check(result):
            self.assertEqual(result, 10, "Should exit with exit code to "
                             "match the wrapped script")
        return proto.done.addCallback(check)


def runScript(executable, args, stdin=[], usePTY=False):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.abspath('..')
    env['COVERAGE_PROCESS_START'] = os.path.abspath('../.coveragerc')
    proto = StdinProtocol(stdin)
    reactor.spawnProcess(proto, executable, args, env=env,
                         usePTY=usePTY)
    return proto


class listTest(TestCase):

    timeout = 2

    @defer.inlineCallbacks
    def test_list(self):
        """
        The C{list} command should list institutions.
        """
        proto = runScript('../bin/banka', ['banka', 'list'])
        rc = yield proto.done
        self.assertEqual(rc, 0)

        self.assertEqual(proto.stderr.getvalue(), '')
        expected = '\n'.join(directory.names()) + '\n'
        self.assertEqual(proto.stdout.getvalue(), expected,
                         "Should write names to stdout")

    @defer.inlineCallbacks
    def test_listVerbose(self):
        """
        The C{list} command in verbose mode should also list the institution
        name and available scripts.
        """
        proto = runScript('../bin/banka', ['banka', 'list', '-v'])
        rc = yield proto.done
        self.assertEqual(rc, 0)

        expected_lines = []
        for name in directory.names():
            details = directory.details(name)
            expected_lines.append('%s scripts: %s domain: %s name: %s' % (
                                  name,
                                  ','.join(sorted(details['scripts'])),
                                  details['info']['domain'],
                                  details['info']['name']))
        expected = '\n'.join(expected_lines) + '\n'
        self.assertEqual(proto.stdout.getvalue(), expected,
                         "Should write names and other deets to stdout")

    @defer.inlineCallbacks
    def test_list_json(self):
        """
        You can get everything in a json format.
        """
        proto = runScript('../bin/banka', ['banka', 'list', '--json'])
        rc = yield proto.done
        self.assertEqual(rc, 0)

        expected = {}
        for name in directory.names():
            details = directory.details(name)
            expected[name] = details
        expected = json.dumps(expected, indent=2) + '\n'
        self.assertEqual(proto.stdout.getvalue(), expected,
                         "Should write everything as JSON")

    @defer.inlineCallbacks
    def test_list_json_include(self):
        """
        You can filter the json output to only include the specified names.
        """
        proto = runScript('../bin/banka', ['banka', 'list', '--json',
                                           '--include=americafirst.com'])
        rc = yield proto.done
        self.assertEqual(rc, 0)

        expected = {}
        details = directory.details('americafirst.com')
        expected[details['dirname']] = details
        expected = json.dumps(expected, indent=2) + '\n'
        self.assertEqual(proto.stdout.getvalue(), expected,
                         "Should write just the chosen inst as JSON")

    @defer.inlineCallbacks
    def test_list_yaml(self):
        """
        You can get everything in a YAML format.
        """
        proto = runScript('../bin/banka', ['banka', 'list', '--yaml'])
        rc = yield proto.done
        self.assertEqual(rc, 0)

        expected = {}
        for name in directory.names():
            details = directory.details(name)
            expected[name] = details
        expected = yaml.dump(expected) + '\n'
        self.assertEqual(proto.stdout.getvalue(), expected,
                         "Should write everything as YAML")
