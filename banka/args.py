# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import argparse
from datetime import datetime


def strToDatetime(s):
    """

    """
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
    ]
    for format in formats:
        try:
            return datetime.strptime(s, format)
        except:
            pass
    raise argparse.ArgumentTypeError('Could not convert %r to datetime' % (s,))
