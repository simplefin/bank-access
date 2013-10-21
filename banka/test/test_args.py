from unittest import TestCase
from datetime import datetime


from bank.args import convertToDatetime


class convertToDatetimeTest(TestCase):


    def test_YYYYMMDD(self):
        r = convertToDatetime('2001-01-01')
        self.assertEqual(r, datetime(2001, 1, 1))
