# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from unittest import TestCase
from datetime import datetime
import argparse

from banka.args import strToDatetime


class strToDatetimeTest(TestCase):

    def test_YYYYMMDD(self):
        r = strToDatetime('2001-01-01')
        self.assertEqual(r, datetime(2001, 1, 1))

    def test_YYYYMMDDTHHMMSS(self):
        r = strToDatetime('2001-01-01T23:12:13')
        self.assertEqual(r, datetime(2001, 1, 1, 23, 12, 13))

    def test_error(self):
        """
        argparse.ArgumentTypeError should be raised for invalid things.
        """
        self.assertRaises(argparse.ArgumentTypeError, strToDatetime, 'foo')
