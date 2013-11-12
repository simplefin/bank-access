# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import yaml
import requests
from StringIO import StringIO

from ofxparse.ofxparse import AccountType, OfxParser

from banka.prompt import prompt
from banka.ofx.template import OFX103RequestMaker


class OFXClient(object):
    """
    XXX
    """

    _ofxParser = OfxParser
    domain = None
    ofx_url = None
    ofx_fi_id = None
    ofx_fi_org = None
    _credentials = None

    def __init__(self, _prompt=None):
        """
        @param _prompt: A function to use for sensitive data prompting.
        """
        self.prompt = _prompt or prompt
        self.requests = requests
        self.requestMaker = OFX103RequestMaker()

    def readServerDetails(self, filename):
        """
        Read the server connection details from a YAML file.

        @param filename: path to YAML file with OFX details.
        """
        fh = open(filename, 'rb')
        info = yaml.load(fh)
        fh.close()

        self.domain = info['domain']

        ofx_info = info['ofx']
        self.ofx_url = ofx_info['url']
        self.ofx_fi_id = str(ofx_info['fi_id'])
        self.ofx_fi_org = str(ofx_info['fi_org'])

    def loginCredentials(self):
        """
        Get the user's login credentials by prompting if necessary.
        """
        if self._credentials:
            return self._credentials
        self._credentials = {}
        self._credentials['user_login'] = self.prompt('_login')
        self._credentials['user_password'] = self.prompt('password')
        return self._credentials

    def parseAccountList(self, ofx):
        """
        Parse an Ofx object into a list of account dictionaries.
        """
        ret = []
        for account in ofx.accounts:
            if account.type == AccountType.Bank:
                ret.append({
                    'routing_number': account.routing_number,
                    'account_number': account.account_id,
                    'account_type': 'bank',
                    'bank_account_type': account.account_type,
                })
            else:
                ret.append({
                    'account_number': account.account_id,
                    'account_type': 'creditcard',
                })
        return ret

    def _parseOfx(self, text):
        """
        Convert an OFX string to an OFX object.
        """
        return self._ofxParser(StringIO(text))

    def requestAccountList(self):
        """
        Connect to the OFX server and get a list of accounts.  Will prompt
        for account credentials if necessary.
        """
        credentials = self.loginCredentials()
        payload = self.requestMaker.accountInfo(self.ofx_fi_org,
                                                self.ofx_fi_id,
                                                credentials['user_login'],
                                                credentials['user_password'])
        headers = self.requestMaker.httpHeaders()
        response = self.requests.post(self.ofx_url,
                                      data=payload, headers=headers)
        ofx = self._parseOfx(response.text)
        return self.parseAccountList(ofx)
