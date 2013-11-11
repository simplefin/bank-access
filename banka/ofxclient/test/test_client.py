# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath

from mock import create_autospec

from ofxparse.ofxparse import Ofx, Account, AccountType

from banka.prompt import prompt
from banka.ofxclient.client import OFXClient
from banka.ofxclient.template import OFX103RequestMaker


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

    def test_readServerDetails(self):
        """
        Should read server details from a info.yml file.
        """
        info = FilePath(self.mktemp())
        info.setContent('---\n'
                        'ofx:\n'
                        '  url: https://example.com\n'
                        '  fi_id: 1234\n'
                        '  fi_org: Some Org\n')

        x = OFXClient()
        x.readServerDetails(info.path)
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
                'account_type_string': 'CHECKING',
                'account_type': 'bank',
            },
            {
                'account_number': '11113',
                'account_type': 'creditcard',
            },
        ])
