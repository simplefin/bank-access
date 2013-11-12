# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
import json
from decimal import Decimal


def ofxToDict(ofx, domain):
    """
    Convert an L{ofxparse.ofxparse.Ofx} object to a dictionary of the
    SimpleFIN persuasion.

    @param domain: Domain of bank (e.g. C{"example.com"})
    """
    accounts = []
    for account in ofx.accounts:
        stmt = account.statement
        transactions = []
        for transaction in stmt.transactions:
            transactions.append({
                'id': transaction.id,
                'posted': transaction.date,
                'amount': transaction.amount,
                'description': transaction.memo,
            })
        accounts.append({
            'org': {
                'domain': domain,
                'sfin-url': None,
            },
            '_insecure_id': account.account_id,
            'name': account.account_type,
            'currency': stmt.currency,
            'balance': stmt.balance,
            'available-balance': stmt.available_balance,
            'balance-as-of': stmt.end_date,
            'transactions': transactions,
        })
    return {
        'accounts': accounts,
    }


def _defaultSerializer(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    else:
        try:
            return obj.isoformat()
        except:
            pass
    raise TypeError("Could not serialize object: %r" % (obj,))


def toJson(obj):
    return json.dumps(obj, default=_defaultSerializer)
