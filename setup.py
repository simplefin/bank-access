# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from setuptools import setup
from setuptools.command.install import install as _install
from pip.req import parse_requirements

import re
import os

def getVersion():
    """
    Get version from version file without importing.
    """
    r = re.compile(r'__version__ = "(.*?)"')
    version_file = os.path.join(os.path.dirname(__file__), 'banka/version.py')
    fh = open(version_file, 'rb')
    for line in fh.readlines():
        m = r.match(line)
        if m:
            return m.groups()[0]

def instFiles():
    """
    Get a list of all the institution-specific files.
    """
    inst_dir = os.path.join(os.path.dirname(__file__), 'banka/inst')
    children = os.listdir(inst_dir)
    return ['inst/%s/*' % (x,) for x in children]


def getRequirements():
    reqs = []
    for req in parse_requirements('requirements.txt'):
        reqs.append(str(req.req))
    return reqs


def zipTrees(a, b):
    for child in os.listdir(a):
        a_child = os.path.join(a, child)
        b_child = os.path.join(b, child)
        yield (a_child, b_child)
        if os.path.isdir(a_child):
            for x in zipTrees(a_child, b_child):
                yield x


def copyPermissions(src, dst):
    """
    For every file in C{dst}, copy the permissions/mode from the corresponding
    file in C{src}.
    """
    import shutil
    for d, s in zipTrees(dst, src):
        print 'copy mode to %s' % (d,)
        shutil.copymode(s, d)


inst_files = instFiles()

class install(_install):

    def run(self):
        _install.run(self)
        print 'Copy over file mode on inst files'
        dst_inst_root = os.path.join(self.install_lib, 'banka/inst')
        src_inst_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'banka/inst'))
        copyPermissions(src_inst_root, dst_inst_root)
        print self.install_lib


setup(
    url='none',
    author='Matt Haggard',
    author_email='matt@simplefin.org',
    name='banka',
    version=getVersion(),
    packages=[
        'banka', 'banka.test',
        'banka.ofx', 'banka.ofx.test',
    ],
    scripts=[
        'bin/banka',
    ],
    install_requires=getRequirements(),
    package_data={
        'banka': inst_files,
    },
    cmdclass={
        'install': install,
    }
)
