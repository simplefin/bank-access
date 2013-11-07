# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from jinja2 import DictLoader

v103_base = '''OFXHEADER:100
DATA:OFXSGML
VERSION:103
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
{% block body %}{% endblock %}
</OFX>

'''

v103_signon = '''<SIGNONMSGSRQV1>
    <SONRQ>
        <DTCLIENT>{{ now }}
        <USERID>{{ user_login }}
        <USERPASS>{{ user_password }}
        <LANGUAGE>ENG
        <FI>
            <ORG>{{ fi_org }}
            <FID>{{ fi_id }}
        </FI>
        <APPID>{{ app_id }}
        <APPVER>{{ app_version }}
    </SONRQ>
</SIGNONMSGSRQV1>
'''

v103_accountInfo = '''{% extends 'base' %}

{% block body %}{% include 'signon' %}
<SIGNUPMSGSRQV1>
    <ACCTINFOTRNRQ>
        <TRNUID>{{ ofx_transaction_id }}
        <ACCTINFORQ>
            <DTACCTUP>20050101
        </ACCTINFORQ>
    </ACCTINFOTRNRQ>
</SIGNUPMSGSRQV1>{% endblock %}'''

v103_statementRequest = '''<STMTTRNRQ>
        <TRNUID>{{ account.ofx_trans_id }}
        <STMTRQ>
            <BANKACCTFROM>
                <BANKID>{{ account.routing_number }}
                <ACCTID>{{ account.account_number }}
                <ACCTTYPE>{{ account.account_type }}
            </BANKACCTFROM>
            <INCTRAN>
                <DTSTART>{{ start_date }}
                <DTEND>{{ end_date }}
                <INCLUDE>Y
            </INCTRAN>
        </STMTRQ>
    </STMTTRNRQ>'''

v103_accountStatements = '''{% extends 'base' %}

{% block body %}{% include 'signon' %}
<BANKMSGSRQV1>{% for account in accounts %}
    {% include 'statementRequest' %}{% endfor %}
</BANKMSGSRQV1>{% endblock %}
'''

v103_templates = {
    'base': v103_base,
    'signon': v103_signon,
    'accountInfo': v103_accountInfo,
    'accountStatements': v103_accountStatements,
    'statementRequest': v103_statementRequest,
}
v103 = DictLoader(v103_templates)
