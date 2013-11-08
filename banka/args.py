# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import argparse
from datetime import datetime, timedelta


def strToDatetime(s):
    """
    Convert a string to a C{datetime}.
    """
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S.%f',
    ]
    for format in formats:
        try:
            return datetime.strptime(s, format)
        except:
            pass
    raise argparse.ArgumentTypeError('Could not convert %r to datetime' % (s,))


def strToDate(s):
    """
    Convert a string to a C{date}.
    """
    return strToDatetime(s).date()


def listAccountsParser():
    """
    Get an argument parser suitable for a list-accounts script.
    """
    today = datetime.now().date()
    default_start_date = today - timedelta(days=8)

    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', dest='start_date', type=strToDate,
                        default=default_start_date)
    parser.add_argument('--end-date', dest='end_date', type=strToDate)
    return parser
