# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase

import difflib
from datetime import datetime, date

from ofxparse.ofxparse import OfxParser

from banka.ofx.template import OFX103RequestMaker


def diffText(a, b, nameA=None, nameB=None):
    alines = [x+'\n' for x in a.split('\n')]
    blines = [x+'\n' for x in b.split('\n')]
    return ''.join(difflib.unified_diff(alines, blines,
                                        fromfile=nameA,
                                        tofile=nameB))


class OFX103RequestMakerTest(TestCase):

    def assertBlobsEqual(self, expected, actual):
        self.assertEqual(expected, actual, 'Difference:\n%s' % (
                         diffText(expected, actual, 'expected', 'actual')))

    def test_httpHeaders(self):
        """
        Should have content-type set
        """
        maker = OFX103RequestMaker()
        headers = maker.httpHeaders()
        self.assertEqual(headers['Content-Type'], 'application/x-ofx')

    def test_now(self):
        """
        By default, the now function should return the current UTC time.
        """
        before = datetime.utcnow().replace(microsecond=0)
        maker = OFX103RequestMaker()
        now = maker.now()
        now = OfxParser.parseOfxDateTime(now)
        after = datetime.utcnow().replace(microsecond=0)
        self.assertTrue(before <= now, 'Expected %r <= %r' % (before, now))
        self.assertTrue(now <= after, 'Expected %r <= %r' % (now, after))

    def test_makeTransId(self):
        """
        This should provide unique, numeric ids.
        """
        maker = OFX103RequestMaker()
        a = maker.makeTransId()
        b = maker.makeTransId()
        self.assertNotEqual(a, b, "Should be different")

    def test_accountInfo(self):
        """
        You can generate the body of a request for getting account information.
        """
        maker = OFX103RequestMaker(transaction_id_generator=lambda: '2222',
                                   _now=lambda: 'CURRENT_TIME')
        body = maker.accountInfo('Org', '4444', '1111', 'password')
        expected = '''OFXHEADER:100
DATA:OFXSGML
VERSION:103
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRQV1>
    <SONRQ>
        <DTCLIENT>CURRENT_TIME
        <USERID>1111
        <USERPASS>password
        <LANGUAGE>ENG
        <FI>
            <ORG>Org
            <FID>4444
        </FI>
        <APPID>QWIN
        <APPVER>1800
    </SONRQ>
</SIGNONMSGSRQV1>
<SIGNUPMSGSRQV1>
    <ACCTINFOTRNRQ>
        <TRNUID>2222
        <ACCTINFORQ>
            <DTACCTUP>20050101
        </ACCTINFORQ>
    </ACCTINFOTRNRQ>
</SIGNUPMSGSRQV1>
</OFX>
'''
        self.assertBlobsEqual(expected, body)
        self.assertEqual(type(body), str, "Should be a string, not unicode")

    def test_accountStatements(self):
        """
        You should be able to generate the body of a request for getting
        account statements.
        """
        trans = ['2222', '2223', '2224']
        maker = OFX103RequestMaker(
            transaction_id_generator=lambda: trans.pop(0),
            _now=lambda: 'CURRENT_TIME')
        body = maker.accountStatements('Org', '4444', '1111', 'password', [
            {
                'account_number': 'ac3333',
                'account_type_string': 'SAVINGS',
                'routing_number': '99999',
            },
            {
                'account_number': 'ac5555',
                'account_type_string': 'CHECKING',
                'routing_number': '88888',
            },
            {
                'account_number': 'cc7777',
                'account_type': 'creditcard',
            },
        ], date(2001, 1, 1), date(2004, 2, 3))
        expected = '''OFXHEADER:100
DATA:OFXSGML
VERSION:103
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRQV1>
    <SONRQ>
        <DTCLIENT>CURRENT_TIME
        <USERID>1111
        <USERPASS>password
        <LANGUAGE>ENG
        <FI>
            <ORG>Org
            <FID>4444
        </FI>
        <APPID>QWIN
        <APPVER>1800
    </SONRQ>
</SIGNONMSGSRQV1>
<BANKMSGSRQV1>
    <STMTTRNRQ>
        <TRNUID>2222
        <STMTRQ>
            <BANKACCTFROM>
                <BANKID>99999
                <ACCTID>ac3333
                <ACCTTYPE>SAVINGS
            </BANKACCTFROM>
            <INCTRAN>
                <DTSTART>20010101
                <DTEND>20040203
                <INCLUDE>Y
            </INCTRAN>
        </STMTRQ>
    </STMTTRNRQ>
    <STMTTRNRQ>
        <TRNUID>2223
        <STMTRQ>
            <BANKACCTFROM>
                <BANKID>88888
                <ACCTID>ac5555
                <ACCTTYPE>CHECKING
            </BANKACCTFROM>
            <INCTRAN>
                <DTSTART>20010101
                <DTEND>20040203
                <INCLUDE>Y
            </INCTRAN>
        </STMTRQ>
    </STMTTRNRQ>
</BANKMSGSRQV1>
<CREDITCARDMSGSRQV1>
    <CCSTMTTRNRQ>
        <TRNUID>2224
        <CCSTMTRQ>
            <CCACCTFROM>
                <ACCTID>cc7777
            </CCACCTFROM>
            <INCTRAN>
                <DTSTART>20010101
                <DTEND>20040203
                <INCLUDE>Y
            </INCTRAN>
        </CCSTMTRQ>
    </CCSTMTTRNRQ>
</CREDITCARDMSGSRQV1>
</OFX>
'''
        self.assertBlobsEqual(expected, body)
        self.assertEqual(type(body), str, "Should be a string, not unicode")

    def test_accountStatements_noCreditcards(self):
        """
        If there are no credit cards, there should be no <CREDITCARDMSGSRQV1>
        section.
        """
        maker = OFX103RequestMaker()
        body = maker.accountStatements('Org', '4444', '1111', 'password', [
            {
                'account_number': 'ac3333',
                'account_type_string': 'SAVINGS',
                'routing_number': '99999',
            },
            {
                'account_number': 'ac5555',
                'account_type_string': 'CHECKING',
                'routing_number': '88888',
            },
        ], date(2001, 1, 1), date(2004, 2, 3))
        self.assertNotIn('<CREDITCARDMSGSRQV1>', body)

    def test_accountStatements_noBankAccounts(self):
        """
        If there are no bank accounts (only credit cards) there should be no
        <BANKMSGSRQV1> section.
        """
        maker = OFX103RequestMaker()
        body = maker.accountStatements('Org', '4444', '1111', 'password', [
            {
                'account_number': 'cc7777',
                'account_type': 'creditcard',
            },
        ], date(2001, 1, 1), date(2004, 2, 3))
        self.assertNotIn('<BANKMSGSRQV1>', body)

    def test_accountStatements_noEndDate(self):
        """
        If no end_date is given, leave off that element.
        """
        maker = OFX103RequestMaker()
        body = maker.accountStatements('Org', '4444', '1111', 'password', [
            {
                'account_number': 'ac3333',
                'account_type_string': 'SAVINGS',
                'routing_number': '99999',
            },
            {
                'account_number': 'cc7777',
                'account_type': 'creditcard',
            },
        ], date(2001, 1, 1))
        self.assertNotIn('<DTEND>', body)
