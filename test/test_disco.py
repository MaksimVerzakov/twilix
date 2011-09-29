import unittest

from twisted.words.protocols.jabber.jid import JID

from twilix import disco, errors
from twilix.stanzas import Iq, Query
from twilix.fields import NodeProp

from twilix.test import dispatcherEmul, hostEmul

class TestVDiscoItemsQuery(unittest.TestCase):
    
    def setUp(self):
        self.query = disco.VDiscoItemsQuery(parent=Iq(type_='set'))
        self.query.host = hostEmul(static_items={'':disco.DiscoItemsQuery()},
                                   static_info={'':disco.DiscoInfoQuery()})
    
    def test_getHandler(self):
        res = self.query.getHandler()
        self.assertTrue(isinstance(res, Iq))
        self.assertTrue(isinstance(res.children[0], Query))
        self.assertEqual(res.children[0].elementUri, 
                         'http://jabber.org/protocol/disco#items')
        self.query.node = 'v'
        res = self.query.getHandler()
        self.assertEqual(res, None)


class TestNotFoundQuery(unittest.TestCase):

    def test_anyHandler(self):
        func = disco.NotFoundQuery().anyHandler
        self.assertRaises(errors.ItemNotFoundException, func)

        
class TestVDiscoInfoQuery(unittest.TestCase):
    
    def setUp(self):
        self.query = disco.VDiscoInfoQuery(parent=Iq(type_='set'))
        self.query.host = hostEmul(static_items={'':disco.DiscoItemsQuery()},
                                   static_info={'':disco.DiscoInfoQuery()})
    
    def test_getHandler(self):
        res = self.query.getHandler()
        self.assertTrue(isinstance(res, Iq))
        self.assertTrue(isinstance(res.children[0], Query))
        self.assertEqual(res.children[0].elementUri, 
                         'http://jabber.org/protocol/disco#info')
        self.query.node = 'v'
        res = self.query.getHandler()
        self.assertEqual(res, None)
        

class TestDisco(unittest.TestCase):
    
    def setUp(self):
        self.disco = disco.Disco(dispatcherEmul('myjid'))
    
    def test_init(self):
        hand=[(dispatcherEmul('jid'), '2'),]
        self.disco.init(handlers=hand)
        test_list=[(disco.VDiscoInfoQuery, self.disco), 
                   (disco.VDiscoItemsQuery, self.disco),
                   (disco.NotFoundDiscoInfoQuery, self.disco), 
                   (disco.NotFoundDiscoItemsQuery, self.disco)]
        test_list.insert(2, hand[0])
        self.assertEqual(self.disco.dispatcher._handlers, test_list)        
    
    def test_getItems(self):
        to = 'somejid'
        self.disco.getItems(to)
        result = self.disco.dispatcher.data[0]
        self.assertEqual(result.type_, 'get')
        self.assertEqual(result.to, JID(to))
        self.assertEqual(result.from_, JID('myjid'))
        self.assertTrue(isinstance(result, Iq))
        
    def test_getInfo(self):
        to = 'somejid'
        self.disco.getInfo(to)
        result = self.disco.dispatcher.data[0]
        self.assertEqual(result.type_, 'get')
        self.assertEqual(result.to, JID(to))
        self.assertEqual(result.from_, JID('myjid'))
        self.assertTrue(isinstance(result, Iq))
