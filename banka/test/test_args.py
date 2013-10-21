# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from unittest import TestCase
from datetime import datetime
import argparse

from banka.args import strToDatetime, listAccountsParser


class strToDatetimeTest(TestCase):

    def test_YYYYMMDD(self):
        r = strToDatetime('2001-01-01')
        self.assertEqual(r, datetime(2001, 1, 1))

    def test_YYYYMMDDTHHMMSS(self):
        r = strToDatetime('2001-01-01T23:12:13')
        self.assertEqual(r, datetime(2001, 1, 1, 23, 12, 13))

    def test_absent_T(self):
        """
        If a space instead of a T is used, it's okay.
        """
        r = strToDatetime('2001-01-01 23:12:13')
        self.assertEqual(r, datetime(2001, 1, 1, 23, 12, 13))
        r = strToDatetime('2001-01-01 23:12:13.394420')
        self.assertEqual(r, datetime(2001, 1, 1, 23, 12, 13, 394420))

    def test_microseconds(self):
        r = strToDatetime('2013-10-21T10:49:36.394420')
        self.assertEqual(r, datetime(2013, 10, 21, 10, 49, 36, 394420))

    def test_error(self):
        """
        argparse.ArgumentTypeError should be raised for invalid things.
        """
        self.assertRaises(argparse.ArgumentTypeError, strToDatetime, 'foo')


class listAccountsParserTest(TestCase):

    def test_start_date(self):
        """
        Should parse the start_date option.
        """
        parser = listAccountsParser()
        args = parser.parse_args(['--start-date', '2001-01-01'])
        self.assertEqual(args.start_date, datetime(2001, 1, 1))

    def test_end_date(self):
        """
        Should parse the end_date option
        """
        parser = listAccountsParser()
        args = parser.parse_args(['--end-date', '2001-02-02'])
        self.assertEqual(args.end_date, datetime(2001, 2, 2))
