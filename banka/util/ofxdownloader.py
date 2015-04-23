#!/usr/bin/env python
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

import os
import yaml
import requests
import json
import argparse

from functools import partial
from uuid import uuid4

from ofxclient import Institution

from decimal import Decimal


def ofxToDict(accounts, days=2, domain=None, id_getter=None):
    """
    Convert a list of L{ofxparse.ofxparse.Account} objects to a
    dictionary of the SimpleFIN persuasion.

    @param accounts: List of Account objects.
    @param days: Number of days back to look for transaction data.
    @param domain: Domain of bank (e.g. C{"example.com"})
    """
    id_getter = id_getter or (lambda x:str(uuid4()))
    ret = []
    for account in accounts:
        stmt = account.statement(days=days)
        transactions = []
        for transaction in stmt.transactions:
            transactions.append({
                'id': transaction.id,
                'posted': transaction.date,
                'amount': transaction.amount,
                'description': '%s %s' % (transaction.payee, transaction.memo),
            })
        ret.append({
            'org': {
                'domain': domain,
                'sfin-url': None,
            },
            # XXX would number_masked be sufficient here?
            'id': id_getter(account.number),
            'name': account.description,
            'currency': stmt.currency,
            'balance': stmt.balance,
            'available-balance': stmt.available_balance,
            'balance-as-of': stmt.end_date,
            'transactions': transactions,
        })
    return {
        'accounts': ret,
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


def getValue(url, key, prompt=None):
    """
    Get a value from the key-value store.
    """
    params = None
    if prompt:
        params = {'prompt': prompt}
    r = requests.get('%s/%s' % (url, key), params=params)
    if not r.ok:
        raise Exception("Request for %r failed: %r" % (key, r.text))
    return r.text


def getID(url, value):
    """
    Exchange a sensitive value for a consistent, benign one.
    """
    r = requests.post(url, {
        'value': value,
    })
    if not r.ok:
        raise Exception("Request to exchange id failed: %r" % (r.text,))
    return r.text


def listTransactions(kvstore_url, days, fi_id, fi_org, url, ofx_version, domain):
    """
    Get SimpleFIN-style list of accounts and transactions.
    """
    username = getValue(kvstore_url, 'username', 'Account/Username?')
    password = getValue(kvstore_url, 'password', 'Password/PIN?')

    inst = Institution(
        id=fi_id,
        org=fi_org,
        url=url,
        username=username,
        password=password,
        client_args={
            'ofx_version': ofx_version,
        })
    accounts = inst.accounts()
    return ofxToDict(accounts, days=days,
        domain=domain,
        id_getter=partial(getID, kvstore_url))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='You must provide '
        'a DATASTORE_URL as an environment variable in order for '
        'this to work.')

    parser.add_argument('--days', '-d',
        default=2,
        type=int,
        help='Days back to get transaction data for. '
             '(default: %(default)s)')
    parser.add_argument('--info-file', '-i',
        required=True,
        help='Path to info.yml file with "ofx" section.'
             '  It should have values for id, org, url and optionally version.')
    args = parser.parse_args()

    kvstore_url = os.environ['DATASTORE_URL']
    data = yaml.load(open(args.info_file, 'rb'))
    ofx = data['ofx']
    trans = listTransactions(
        kvstore_url=kvstore_url,
        days=args.days,
        fi_id=str(ofx['id']),
        fi_org=ofx['org'],
        url=ofx['url'],
        ofx_version=str(ofx.get('version', '102')),
        domain=data['domain'])
    print toJson(trans)
