# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from setuptools import setup
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
        'banka': instFiles(),
    },
)
