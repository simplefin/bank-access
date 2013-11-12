# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from datetime import datetime
from uuid import uuid4

from jinja2 import Environment, StrictUndefined

from banka.ofx.template_data import v103


class OFX103RequestMaker(object):
    """
    I make the bodies of the various request types for OFX 1.0.3.

    @ivar app_id: Name we identify as to the OFX server.  Some servers use
        this to determine whether or not to accept the request.
    @ivar app_version: Version string of the app.  See ^
    """

    app_id = 'QWIN'
    app_version = '1800'

    def __init__(self, transaction_id_generator=None, _now=None):
        self.now = _now or self.now
        self.makeTransId = transaction_id_generator or self.makeTransId
        self.jinja_env = Environment(undefined=StrictUndefined,
                                     loader=v103)

    def now(self):
        """
        Return a string current time.
        """
        _now = datetime.utcnow()
        return _now.strftime('%Y%m%d%H%M%S.000[+0:UTC]')

    def makeTransId(self):
        """
        Return a unique transaction id
        """
        return str(uuid4()).replace('-', '')

    def httpHeaders(self):
        """
        Get the headers for an HTTP request.
        """
        return {
            'Content-Type': 'application/x-ofx',
        }

    def accountInfo(self, fi_org, fi_id, user_login, user_password):
        """
        Generate a request body for requesting an account listing.

        @param fi_org: Financial Institution Organization name
        @param fi_id: Financial Institution ID
        @param user_login: Login name for server.
        @param user_password: Password for server.
        """
        params = {
            'now': self.now(),
            'ofx_transaction_id': self.makeTransId(),
            'app_id': self.app_id,
            'app_version': self.app_version,
            'user_login': user_login,
            'user_password': user_password,
            'fi_org': fi_org,
            'fi_id': fi_id,
        }
        template = self.jinja_env.get_template('accountInfo')
        # XXX should this be utf-8 when the header specifies USASCII?
        return template.render(params).encode('utf-8')

    def accountStatements(self, fi_org, fi_id, user_login, user_password,
                          accounts, start_date, end_date=None):
        """
        Generate a request body for requesting account transactions.
        """
        bank_accounts = []
        creditcards = []
        for account in accounts:
            account['ofx_trans_id'] = self.makeTransId()
            if account.get('account_type', 'bank_account') == 'bank_account':
                bank_accounts.append(account)
            else:
                creditcards.append(account)
        if end_date:
            end_date = end_date.strftime('%Y%m%d')
        params = {
            'now': self.now(),
            'app_id': self.app_id,
            'app_version': self.app_version,
            'user_login': user_login,
            'user_password': user_password,
            'fi_org': fi_org,
            'fi_id': fi_id,
            'bank_accounts': bank_accounts,
            'creditcards': creditcards,
            'start_date': start_date.strftime('%Y%m%d'),
            'end_date': end_date,
        }
        template = self.jinja_env.get_template('accountStatements')
        return template.render(params).encode('utf-8')
