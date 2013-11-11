# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import yaml
from banka.prompt import prompt


class OFXClient(object):
    """
    XXX
    """

    prompt = prompt

    ofx_url = None
    ofx_fi_id = None
    ofx_fi_org = None
    _credentials = None

    def __init__(self, _prompt=None):
        """
        @param _prompt: A function to use for sensitive data prompting.
        """
        self.prompt = _prompt or self.prompt

    def readServerDetails(self, filename):
        """
        Read the server connection details from a YAML file.

        @param filename: path to YAML file with OFX details.
        """
        fh = open(filename, 'rb')
        info = yaml.load(fh)
        fh.close()

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
