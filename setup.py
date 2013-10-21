# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from distutils.core import setup


setup(
    url='none',
    author='Matt Haggard',
    author_email='matt@simplefin.org',
    name='banka',
    version='0.1',
    packages=[
        'banka', 'banka.test',
    ],
    scripts=[
        'bin/banka',
    ]
)
