# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath

from mock import create_autospec, MagicMock

from StringIO import StringIO

import requests

from ofxparse.ofxparse import Ofx, Account, AccountType, OfxParser

from banka.prompt import prompt, alias, replaceInsecureIDs
from banka.ofx.client import OFXClient
from banka.ofx.template import OFX103RequestMaker
from banka.ofx.parse import ofxToDict


class OFXClientTest(TestCase):

    def test_defaultPrompter(self):
        """
        By default, the banka.prompt.prompt function is used for prompting.
        """
        x = OFXClient()
        self.assertEqual(x.prompt, prompt, "Should use the default prompt "
                         "function")

    def test_overridePrompt(self):
        """
        You can override the prompt function on initialization
        """
        x = OFXClient(_prompt='foo')
        self.assertEqual(x.prompt, 'foo')

    def test_defaultRequester(self):
        """
        By default, the L{requests} library is used for making requests.
        """
        x = OFXClient()
        self.assertEqual(x.requests, requests)

    def test_readServerDetails(self):
        """
        Should read server details from a info.yml file.
        """
        info = FilePath(self.mktemp())
        info.setContent('---\n'
                        'domain: foo.com\n'
                        'ofx:\n'
                        '  url: https://example.com\n'
                        '  fi_id: 1234\n'
                        '  fi_org: Some Org\n')

        x = OFXClient()
        x.readServerDetails(info.path)
        self.assertEqual(x.domain, 'foo.com')
        self.assertEqual(x.ofx_url, 'https://example.com')
        self.assertEqual(x.ofx_fi_id, '1234')
        self.assertEqual(x.ofx_fi_org, 'Some Org')

    def test_loginCredentials(self):
        """
        Calling loginCredentials the first time should result in a prompt to
        the parent process.  Calling subsequent times should use cached
        versions of the credentials.
        """
        data = {
            '_login': 'joe',
            'password': '123',
        }
        fake_prompt = create_autospec(prompt,
                                      side_effect=lambda key: data[key])

        x = OFXClient(_prompt=fake_prompt)

        # first call
        creds = x.loginCredentials()
        fake_prompt.assert_any_call('_login')
        fake_prompt.assert_any_call('password')
        self.assertEqual(creds['user_login'], 'joe')
        self.assertEqual(creds['user_password'], '123')

        # second call
        fake_prompt.mock.reset_mock()
        creds = x.loginCredentials()
        self.assertEqual(fake_prompt.call_count, 0, "Should not prompt on "
                         "subsequent calls for the credentials")

    def test_requestMaker(self):
        """
        The default OFX Requests Maker is the L{OFX103RequestMaker}.
        """
        x = OFXClient()
        self.assertTrue(isinstance(x.requestMaker, OFX103RequestMaker))

    def test_parseAccountList(self):
        """
        C{parseAccountList} should turn an account list OFX object (from the
        C{ofxparser} library) into a list of dictionaries suitable for use
        in the requestMaker.
        """
        ofx = Ofx()

        account1 = Account()
        account1.routing_number = 'router1'
        account1.account_id = '11112'
        account1.account_type = 'CHECKING'
        account1.type = AccountType.Bank

        account2 = Account()
        account2.account_id = '11113'
        account2.type = AccountType.CreditCard

        ofx.accounts = [account1, account2]

        x = OFXClient()
        accounts = x.parseAccountList(ofx)
        self.assertEqual(accounts, [
            {
                'routing_number': 'router1',
                'account_number': '11112',
                'bank_account_type': 'CHECKING',
                'account_type': 'bank',
            },
            {
                'account_number': '11113',
                'account_type': 'creditcard',
            },
        ])

    def test__parseOfx(self):
        """
        _parseOfx should pass a StringIO to _ofxParser and return the result.
        """
        x = OFXClient()
        self.assertEqual(x._ofxParser, OfxParser)

        x._ofxParser = MagicMock()
        x._ofxParser.parse.return_value = 'foo'
        result = x._parseOfx('hey')
        self.assertEqual(x._ofxParser.parse.call_count, 1)
        arg = x._ofxParser.parse.call_args[0][0]
        self.assertTrue(isinstance(arg, StringIO))
        self.assertEqual(arg.getvalue(), 'hey')
        self.assertEqual(result, 'foo')

    def test__ofxToDict(self):
        """
        _ofxToDict should be L{banka.ofx.parse.ofxToDict} by default.
        """
        x = OFXClient()
        self.assertEqual(x._ofxToDict, ofxToDict)

    def test__alias(self):
        """
        C{_alias} should be L{banka.prompt.alias} by default.
        """
        x = OFXClient()
        self.assertEqual(x._alias, alias)

    def test__replaceInsecureIDs(self):
        """
        C{_replaceInsecureIDs} should be L{banka.prompt.replaceInsecureIDs}
        by default.
        """
        x = OFXClient()
        self.assertEqual(x._replaceInsecureIDs, replaceInsecureIDs)

    def test_requestAccountList(self):
        """
        Requesting an account list should get the credentials, use the
        C{requestMaker} to generate payload and headers, post to an OFX server
        then parse the result, returning a dictionary of accounts.
        """
        x = OFXClient()

        # faking, faking, faking
        response = MagicMock()
        response.text = 'The response text'

        original = x.requests.post
        self.addCleanup(setattr, x.requests, 'post', original)
        x.requests.post = create_autospec(x.requests.post,
                                          return_value=response)
        x.loginCredentials = create_autospec(x.loginCredentials, return_value={
            'user_login': '12345678',
            'user_password': 'password',
        })
        x.requestMaker.accountInfo = create_autospec(
            x.requestMaker.accountInfo,
            return_value='payload')
        x.parseAccountList = create_autospec(x.parseAccountList,
                                             return_value='account list')
        x._parseOfx = create_autospec(x._parseOfx, return_value='return ofx')

        x.ofx_url = 'https://ofx.example.com'
        x.ofx_fi_id = '1234'
        x.ofx_fi_org = 'Some Bank'

        account_list = x.requestAccountList()
        x.loginCredentials.assert_called_once_with()
        x.requestMaker.accountInfo.assert_called_once_with('Some Bank',
                                                           '1234',
                                                           '12345678',
                                                           'password')
        headers = x.requestMaker.httpHeaders()
        x.requests.post.assert_called_once_with('https://ofx.example.com',
                                                data='payload',
                                                headers=headers)
        x._parseOfx.assert_called_once_with('The response text')
        x.parseAccountList.assert_called_once_with('return ofx')
        self.assertEqual(account_list, 'account list')

    def test_requestStatements(self):
        """
        Requesting statements should get the credentials, use the
        C{requestMaker} to generate a payload and headers, post to an OFX
        server, then parse the result, transforming it into a dictionary.
        """
        x = OFXClient()

        # faking, faking, faking
        response = MagicMock()
        response.text = 'The response text'

        original = x.requests.post
        self.addCleanup(setattr, x.requests, 'post', original)
        x.requests.post = create_autospec(x.requests.post,
                                          return_value=response)
        x.loginCredentials = create_autospec(x.loginCredentials, return_value={
            'user_login': '12345678',
            'user_password': 'password',
        })
        x.requestMaker.accountStatements = create_autospec(
            x.requestMaker.accountStatements,
            return_value='payload')
        x.parseAccountList = create_autospec(x.parseAccountList,
                                             return_value='account list')
        x._parseOfx = create_autospec(x._parseOfx, return_value='return ofx')
        x._ofxToDict = create_autospec(x._ofxToDict, return_value='the dict')
        x._replaceInsecureIDs = create_autospec(x._replaceInsecureIDs,
                                                return_value='aliased dict')

        x.domain = 'foo.com'
        x.ofx_url = 'https://ofx.example.com'
        x.ofx_fi_id = '1234'
        x.ofx_fi_org = 'Some Bank'

        d = x.requestStatements('accounts', 'start', 'end')
        x.loginCredentials.assert_called_once_with()
        x.requestMaker.accountStatements.assert_called_once_with(
            'Some Bank',
            '1234',
            '12345678',
            'password',
            'accounts',
            'start',
            'end')
        headers = x.requestMaker.httpHeaders()
        x.requests.post.assert_called_once_with('https://ofx.example.com',
                                                data='payload',
                                                headers=headers)
        x._parseOfx.assert_called_once_with('The response text')
        x._ofxToDict.assert_called_once_with('return ofx', 'foo.com')
        x._replaceInsecureIDs.assert_called_once_with(x._alias, 'the dict')
        self.assertEqual(d, 'aliased dict')
