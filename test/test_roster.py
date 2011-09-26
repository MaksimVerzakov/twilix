import unittest

from twilix import roster
from twilix.stanzas import Iq
from twilix.errors import NotAcceptableException
from twilix.test import iqEmul, hostEmul

class hostEmulator(hostEmul):
    def updateRoster(self, smth):
        self.update = True

class TestRosterItem(unittest.TestCase):
    def setUp(self):
        self.ros = roster.RosterItem(jid='jid', nick='name')
        
    def test_is_online(self):
        self.assertEqual(self.ros.is_online(), False)
        self.ros.presences['1'] = 2
        self.assertEqual(self.ros.is_online(), True)
    
    def test_nick_(self):
        pass
        #self.assertEqual(self.ros.nick, 'name')
    
    def test_addGroup(self):
        pass
        #self.ros._groups = []
        #res = self.ros.addGroup('RHCP')
        #self.assertEqual(res, True)
        #res = self.ros.addGroup('RHCP')
        #self.assertEqual(res, None)
    
class TestRosterQuery(unittest.TestCase):
    def test_setHandler(self):
        rq = roster.RosterQuery(parent=Iq(type_='get', id='id0'))
        rq.host = hostEmulator()        
        self.assertEqual(rq.setHandler(), Iq(type_='result', id='id0'))
    
    def test_getHandler(self):
        rq = roster.RosterQuery(parent=Iq(type_='get'))
        self.assertRaises(NotAcceptableException, rq.getHandler)
