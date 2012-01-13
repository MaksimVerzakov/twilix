import unittest

from twisted.words.protocols.jabber.jid import JID
from twisted.internet.defer import Deferred

from twilix.vcard import MyVCardQuery, VCard, VCardQuery
from twilix.stanzas import Iq
from twilix import errors

from twilix.test import dispatcherEmul, iqEmul, hostEmul


class TestVCardQuery(unittest.TestCase):
    
    def setUp(self):
        self.MyVCardQuery = MyVCardQuery(parent=Iq(type_='result', 
                                         to='somejid'))
        disp = dispatcherEmul('somejid')
        self.vc = VCardQuery(name='John')
        host = hostEmul(myvcard=self.vc, dispatcher=disp)
        self.MyVCardQuery.host = host         
        self.VCard = VCard(disp, self.vc)
    
    def test_getHandler(self):
        res = self.MyVCardQuery.getHandler()
        self.assertTrue(self.vc in res.children)
        self.MyVCardQuery.host.myvcard = None
        self.assertRaises(errors.ItemNotFoundException, 
                          self.MyVCardQuery.getHandler)
        
    def test_setHandler(self):
        self.assertRaises(errors.ForbiddenException, 
                          self.MyVCardQuery.setHandler)


class TestVCard(unittest.TestCase):
    
    def setUp(self):
        self.VC = VCard(dispatcher=dispatcherEmul('jid'))
    
    def test_init(self):
        hand=[(dispatcherEmul('jid'), '2'),]
        self.VC.init(handlers=hand)
        hand.insert(0, (MyVCardQuery, self.VC))
        self.assertEqual(self.VC.dispatcher._handlers, hand)
    
    def test_get(self):
        to = 'somejid'
        result = self.VC.get(to)
        self.assertTrue(isinstance(result, Deferred))
        result = self.VC.dispatcher.data[0]
        self.assertEqual(result.type_, 'get')
        self.assertEqual(result.to, JID(to))
        self.assertEqual(result.from_, JID('jid'))
        self.assertTrue(isinstance(result, Iq))

    def test_set(self):
        card = VCardQuery(full_name='John')   
        result = self.VC.set(card)    
        self.assertTrue(isinstance(result, Deferred))
        result = self.VC.dispatcher.data[0]
        self.assertEqual(result.type_, 'set')
        self.assertTrue(isinstance(result, Iq))
