import unittest

from twilix.vcard import MyVCardQuery, VCard
from twilix import errors

from twilix.test import dispatcherEmul, iqEmul, hostEmul

class MyVCardQueryEmul(MyVCardQuery):
    iq = iqEmul()


class TestVCardQuery(unittest.TestCase):
    
    def setUp(self):
        self.MyVCardQuery = MyVCardQueryEmul()
        disp = dispatcherEmul('some_jid')
        host = hostEmul(myvcard='myvcard', dispatcher=disp)
        self.MyVCardQuery.host = host         
        self.VCard = VCard(disp, 'myvcard')
    
    def test_getHandler(self):
        res = self.MyVCardQuery.getHandler()
        self.assertTrue('myvcard' in res.children)
        self.MyVCardQuery.host.myvcard = None
        self.assertRaises(errors.ItemNotFoundException, self.MyVCardQuery.getHandler)
        
    def test_setHandler(self):
        self.assertRaises(errors.ForbiddenException, self.MyVCardQuery.setHandler)
