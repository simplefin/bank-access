from ofxclient import Institution
import getpass

inst = Institution(
    id='54324',
    org='America First Credit Union',
    url='https://ofx.americafirst.com',
    username=getpass.getpass('account? '),
    password=getpass.getpass('password? '))
accounts = inst.accounts()
transactions = accounts[0].transactions(days=5)

