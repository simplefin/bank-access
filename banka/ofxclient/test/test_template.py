# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase

import difflib
from datetime import datetime

from ofxparse.ofxparse import OfxParser

from banka.ofxclient.template import OFX103RequestMaker


def diffText(a, b, nameA=None, nameB=None):
    alines = [x+'\n' for x in a.split('\n')]
    blines = [x+'\n' for x in b.split('\n')]
    return ''.join(difflib.unified_diff(alines, blines,
                                        fromfile=nameA,
                                        tofile=nameB))


class OFX103RequestMakerTest(TestCase):

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

    def assertBlobsEqual(self, expected, actual):
        self.assertEqual(expected, actual, 'Difference:\n%s' % (
                         diffText(expected, actual, 'expected', 'actual')))

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
