from twisted.python import FilePath
from ofxhome import OFXHome

items = OFXHome.search()
for item in items:
    bank = OFXHome.lookup(item['id'])
    print bank.name, bank.fid, bank.url, bank.brokerid, bank.org
