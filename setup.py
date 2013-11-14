# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from distutils.core import setup

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
    ]
)
