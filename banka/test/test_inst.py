# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath

from banka.inst import InstitutionDirectory, directory


class InstitutionDirectoryTest(TestCase):

    def test_names(self):
        """
        L{InstitutionDirectory.names} should list all of the subdirectories
        in a directory.
        """
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        tmp.child('foo').makedirs()
        tmp.child('bar').makedirs()
        tmp.child(u'ol\N{SNOWMAN}').makedirs()

        d = InstitutionDirectory(tmp.path)
        names = d.names()
        expected = ['foo', 'bar', u'ol\N{SNOWMAN}'.encode('utf-8')]
        self.assertEqual(names, sorted(expected))

    def test_details(self):
        """
        L{InstitutionDirectory.details} should return a dictionary with
        all the data in the bank's C{info.yml} as well as a listing of
        the other scripts in the directory.
        """
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        foo = tmp.child('foo')
        foo.makedirs()
        foo.child('info.yml').setContent(
            '---\n'
            'name: America First Credit Union\n'
            'domain: americafirst.com\n'
            'maintainers:\n'
            '  - some guy\n'
            'favorite-color: blue\n'
            'favorite:\n'
            '  number: 12\n'
            '  word: torpor\n'
        )
        foo.child('list-accounts').setContent('not a real script')

        d = InstitutionDirectory(tmp.path)
        details = d.details('foo')
        self.assertEqual(details['dirname'], 'foo')
        self.assertEqual(details['info'], {
            'name': 'America First Credit Union',
            'domain': 'americafirst.com',
            'maintainers': ['some guy'],
            'favorite-color': 'blue',
            'favorite': {
                'number': 12,
                'word': 'torpor',
            },
        }, "Should read the info.yml file")
        self.assertEqual(details['scripts'], {
            'list-accounts': {
                'path': foo.child('list-accounts').path,
            }
        }, "Should list all the scripts and their absolute path")


class directoryTest(TestCase):

    def test_path(self):
        """
        The global directory instance should be an L{InstitutionDirectory}
        and should be rooted at C{banka/inst}.
        """
        self.assertTrue(isinstance(directory, InstitutionDirectory))

        banka_root = FilePath(__file__).parent().parent()
        self.assertEqual(directory.fp, banka_root.child('inst'))
