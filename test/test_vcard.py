import unittest
from twilix.vcard import MyVCardQuery, VCard
from twilix import errors

class iqEmul(object):
    to='some_jid'
    children = []
    
    def makeResult(self):
        return self
        
    def link(self, content):
        self.children.append(content)


class dispatcherEmul(object):
    def __init__(self, myjid):
        self.myjid = myjid

        
class hostEmul(object):
    def __init__(self, myvcard, dispatcher):
        self.myvcard = myvcard
        self.dispatcher = dispatcher


class MyVCardQueryEmul(MyVCardQuery):
    iq = iqEmul()


class TestVCardQuery(unittest.TestCase):
    
    def setUp(self):
        self.MyVCardQuery = MyVCardQueryEmul()
        disp = dispatcherEmul('some_jid')
        host = hostEmul('myvcard', disp)
        self.MyVCardQuery.host = host         
        self.VCard = VCard(disp, 'myvcard')
    
    def test_getHandler(self):
        res = self.MyVCardQuery.getHandler()
        self.assertTrue('myvcard' in res.children)
        self.MyVCardQuery.host.myvcard = None
        self.assertRaises(errors.ItemNotFoundException, self.MyVCardQuery.getHandler)
        
    def test_setHandler(self):
        self.assertRaises(errors.ForbiddenException, self.MyVCardQuery.setHandler)
