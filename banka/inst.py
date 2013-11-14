# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

"""
@var directory: An L{InstitutionDirectory} instance pointed at the path within
    this package where the institution scripts live.
"""
from twisted.python.filepath import FilePath
import yaml


class InstitutionDirectory(object):
    """
    I am an interface for reading a directory full of financial
    institution data.
    """

    def __init__(self, path):
        self.fp = FilePath(path)

    def names(self):
        """
        Get a list of institution names.
        """
        return [x.basename() for x in self.fp.children()]

    def details(self, name):
        """
        Get the known details about an institution.
        """
        inst_dir = self.fp.child(name)

        # info
        info = yaml.load(inst_dir.child('info.yml').open())

        # scripts
        scripts = {}
        for child in inst_dir.listdir():
            if child in ['info.yml']:
                continue
            scripts[child] = {
                'path': inst_dir.child(child).path,
            }

        return {
            'dirname': name,
            'info': info,
            'scripts': scripts,
        }

_banka_package = FilePath(__file__).parent()

directory = InstitutionDirectory(_banka_package.child('inst').path)
