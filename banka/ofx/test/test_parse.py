# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase

import json
from datetime import datetime
from decimal import Decimal
from ofxparse.ofxparse import Ofx, Account, Statement, Transaction

from banka.ofx.parse import ofxToDict, toJson


class ofxToDictTest(TestCase):

    def test_basic(self):
        """
        An L{Ofx} object with multiple accounts and transactions should be
        turned into a dict by L{ofxToDict}.
        """
        x = Ofx()

        account1 = Account()
        account1.account_id = 'account1'
        account1.account_type = 'Checking'

        account1.statement = Statement()
        account1.statement.start_date = datetime(2001, 1, 1, 12, 20, 33)
        account1.statement.end_date = datetime(2001, 2, 3, 12, 20, 34)
        account1.statement.balance = Decimal('900.22')
        account1.statement.available_balance = Decimal('925.22')
        account1.statement.currency = 'USD'

        t1 = Transaction()
        t1.id = '0001'
        t1.date = datetime(2001, 1, 15, 8, 8, 8)
        t1.amount = Decimal('12.20')
        t1.memo = 'T1 memo'

        t2 = Transaction()
        t2.id = '0002'
        t2.date = datetime(2001, 1, 20, 9, 9, 9)
        t2.amount = Decimal('-45.22')
        t2.memo = 'T2 memo'

        account1.statement.transactions = [t1, t2]

        account2 = Account()
        account2.account_id = 'account2'
        account2.account_type = 'Savings'

        account2.statement = Statement()
        account2.statement.start_date = datetime(2001, 1, 1, 12, 20, 33)
        account2.statement.end_date = datetime(2001, 2, 3, 12, 20, 34)
        account2.statement.balance = Decimal('100.00')
        account2.statement.available_balance = Decimal('125.00')
        account2.statement.currency = 'USD'
        account2.statement.transactions = []

        x.accounts = [account1, account2]

        d = ofxToDict(x, 'example.com')
        expected = {
            'accounts': [
                {
                    'org': {
                        'domain': 'example.com',
                        'sfin-url': None,
                    },
                    '_insecure_id': 'account1',
                    'name': 'Checking',
                    'currency': 'USD',
                    'balance': Decimal('900.22'),
                    'available-balance': Decimal('925.22'),
                    'balance-as-of': datetime(2001, 2, 3, 12, 20, 34),
                    'transactions': [
                        {
                            'id': '0001',
                            'posted': datetime(2001, 1, 15, 8, 8, 8),
                            'amount': Decimal('12.20'),
                            'description': 'T1 memo',
                        },
                        {
                            'id': '0002',
                            'posted': datetime(2001, 1, 20, 9, 9, 9),
                            'amount': Decimal('-45.22'),
                            'description': 'T2 memo',
                        },
                    ]
                },
                {
                    'org': {
                        'domain': 'example.com',
                        'sfin-url': None,
                    },
                    '_insecure_id': 'account2',
                    'name': 'Savings',
                    'currency': 'USD',
                    'balance': Decimal('100.00'),
                    'available-balance': Decimal('125.00'),
                    'balance-as-of': datetime(2001, 2, 3, 12, 20, 34),
                    'transactions': [],
                }
            ]
        }
        self.assertEqual(d, expected)


class toJsonTest(TestCase):

    def test_Decimal(self):
        """
        C{Decimal}s should be converted to strings.
        """
        self.assertEqual(toJson(Decimal('12.44')), '"12.44"')

    def test_datetime(self):
        """
        C{datetime}s should be converted to iso format.
        """
        self.assertEqual(toJson(datetime(2001, 4, 5, 6, 7, 8)),
                         '"2001-04-05T06:07:08"')

    def test_normal(self):
        """
        Normal things should become normal JSON.
        """
        sample = {'foo': 12, 'bar': [1, 2, 3], 'baz': 'hey'}
        self.assertEqual(toJson(sample), json.dumps(sample))

    def test_TypeError(self):
        """
        Some things can't be serialized.
        """
        self.assertRaises(TypeError, toJson, object())
