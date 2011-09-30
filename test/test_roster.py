import unittest

from twilix import roster
from twilix.stanzas import Iq
from twilix.base import VElement
from twilix.errors import NotAcceptableException
from twilix.test import iqEmul, hostEmul, dispatcherEmul


class itemEmul(VElement):
    presences = []
    subscription = ''


class hostEmulator(hostEmul):
    items = []
    
    def updateRoster(self, smth):
        self.update = True
        
    def getItemByJid(self, jid):
        pass


class queryEmul(object):
    items = ['1', '2', '3']


class TestRosterItem(unittest.TestCase):
    def setUp(self):
        self.ros = roster.RosterItem(jid='jid', nick='name')
        
    def test_is_online(self):
        self.assertEqual(self.ros.is_online(), False)
        self.ros.presences['1'] = 2
        self.assertEqual(self.ros.is_online(), True)
    
    def test_unicode(self):
        self.assertEqual(unicode(self.ros), 
                         "<RosterItem JID(u'jid') name, subscription None>")
                         
    def test_repr(self):
        self.assertEqual(repr(self.ros), 
                         "<RosterItem JID(u'jid') name, subscription None>")
    
   
class TestRosterQuery(unittest.TestCase):
    def test_setHandler(self):
        rq = roster.RosterQuery(parent=Iq(type_='get', id='id0'))
        rq.host = hostEmulator()        
        self.assertEqual(rq.setHandler(), Iq(type_='result', id='id0'))
    
    def test_getHandler(self):
        rq = roster.RosterQuery(parent=Iq(type_='get'))
        self.assertRaises(NotAcceptableException, rq.getHandler)

class TestRoster(unittest.TestCase):
    
    def setUp(self):
        self.rost = roster.Roster(dispatcherEmul('jid'), mypresence='pr')
            
    def test_init(self):
        test_list = [(roster.RosterQuery, self.rost),
                     (roster.RosterPresence, self.rost)]
        self.rost.init()
        self.assertEqual(self.rost.dispatcher._handlers, test_list)
        res = self.rost.dispatcher.data[0]
        self.assertTrue(isinstance(res, Iq))
        self.assertEqual(res.result_class, roster.RosterQuery)
    
    def test_send_initial_presence(self):
        func = self.rost._send_initial_presence
        self.assertRaises(AssertionError, func, 'any')
        func(self.rost)
        self.assertEqual(self.rost.dispatcher.data[0], self.rost.mypresence)
    
    def test_updatePresence(self):
        self.rost.updatePresence('presence')
        self.assertEqual(self.rost.dispatcher.data[0], 'presence')
        self.assertEqual(self.rost.updatePresence(None), None)
    
    def test_gotRoster(self):
        self.rost.gotRoster(queryEmul())
        pass
    
    def test_addItem(self):
        self.rost.addItem(itemEmul())
        self.assertTrue(isinstance(self.rost.dispatcher.data[0], Iq))
        self.assertEqual(self.rost.dispatcher.data[0].type_, 'set')   
        
    def test_removeItem(self):        
        self.rost.removeItem(itemEmul())
        self.assertTrue(isinstance(self.rost.dispatcher.data[0], Iq))
        self.assertEqual(self.rost.dispatcher.data[0].type_, 'set')    

