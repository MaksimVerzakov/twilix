import unittest

from twilix.vcard import MyVCardQuery, VCard, VCardQuery
from twilix.stanzas import Iq
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

class TestVCard(unittest.TestCase):
    
    def setUp(self):
        self.VC = VCard(dispatcher=dispatcherEmul('jid'))
    
    def test_init(self):
        hand=[(dispatcherEmul('jid'), '2'),]
        self.VC.init(handlers=hand)
        hand.insert(0, (MyVCardQuery, self.VC))
        self.assertEqual(self.VC.dispatcher._handlers, hand)
    
    def test_get(self):
        self.VC.get('somejid')
        #import pdb; pdb.set_trace()
        self.assertEqual(self.VC.dispatcher.data, [VCardQuery(parent=Iq(type_='get', to='somejid', from_='jid', id='H_1')).iq,])

    def test_get(self):
        card = VCardQuery(full_name='John')       
        self.VC.set(card)    
        vc =  VCardQuery(parent=Iq(type_='set', id='H_2')).iq
        self.assertEqual(self.VC.dispatcher.data, [vc,])
