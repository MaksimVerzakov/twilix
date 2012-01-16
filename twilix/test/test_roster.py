import unittest
from twisted.trial import unittest

from pydispatch import dispatcher

from twisted.internet import reactor

from twilix import roster
from twilix.stanzas import Iq
from twilix.jid import MyJID
from twilix.base.velement import VElement
from twilix.errors import NotAcceptableException
from twilix.test import iqEmul, hostEmul, dispatcherEmul


class itemEmul(VElement):
    
    def __init__(self, jid, groups=None, subscription='', \
                 presences = {}, **kwargs):
        self.presences = presences
        self.groups = groups
        self.subscription = subscription
        self.jid = MyJID(jid)
        super(itemEmul, self).__init__(**kwargs)     


class hostEmulator(hostEmul):
    roster_got = object()
    roster_item_added = object()
    roster_item_removed = object()
    contact_available = object()
    contact_unavailable = object()
    resource_available = object()
    resource_unavailable = object()
    resource_changed_status = object()

    subscribe = object()
    subscribed = object()
    unsubscribe = object()
    unsubscribed = object()
    
    def updateRoster(self, smth):
        self.update = True
        
    def getItemByJid(self, jid):
        r = None
        jid = jid.bare()
        for i in self.items:
            if jid == i.jid:
                r = i
        return r


class queryEmul(object):
    def __init__(self, items):
        self.items = items


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
        items = [itemEmul('fast@wok'), 
               itemEmul('little@nation', presences={'q':'w', 'r':'t'}), 
               itemEmul('gordon@freeman', presences={'1':'2', '3':'4'})]
        rq.host = hostEmulator(items=items)        
        self.assertEqual(rq.setHandler(), Iq(type_='result', id='id0'))
    
    def test_getHandler(self):
        rq = roster.RosterQuery(parent=Iq(type_='get'))
        self.assertRaises(NotAcceptableException, rq.getHandler)

class TestRoster(unittest.TestCase):
    
    def setUp(self):
        self.rost = roster.Roster(dispatcherEmul('jid'), 
                                  mypresence='pr')        
            
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
        self.assertEqual(self.rost.dispatcher.data[0], 
                         self.rost.mypresence)
    
    def test_updatePresence(self):
        self.rost.updatePresence('presence')
        self.assertEqual(self.rost.dispatcher.data[0], 'presence')
        self.assertEqual(self.rost.updatePresence(None), None)
    
    def test_gotRoster(self):
        self.rost.gotRoster(queryEmul([]))
        pass
    
    def test_addItem(self):
        self.rost.addItem(itemEmul(jid='some@where'))
        self.assertTrue(isinstance(self.rost.dispatcher.data[0], Iq))
        self.assertEqual(self.rost.dispatcher.data[0].type_, 'set')   
        
    def test_removeItem(self):        
        self.rost.removeItem(itemEmul(jid='some@where'))
        self.assertTrue(isinstance(self.rost.dispatcher.data[0], Iq))
        self.assertEqual(self.rost.dispatcher.data[0].type_, 'set') 
    
    def test_updateRoster(self):
        self.rost.items = [itemEmul(jid='amy@wine')]
        items = [itemEmul(subscription='remove', jid='amy@wine'), 
                 itemEmul(subscription='both', jid='sup@per'), 
                 itemEmul(subscription='none', jid='homer@j')]
        q = queryEmul(items)
        self.rost.updateRoster(q)
        self.assertEqual(self.rost.items, items[1:])
    
    def test_getItemByJid(self):
        items = [itemEmul(jid='amy@wine'), 
                 itemEmul(jid='sup@per'), 
                 itemEmul(jid='homer@j')]
        self.rost.items = items
        res = self.rost.getItemByJid(MyJID('somebody@to/love'))
        self.assertEqual(res, None)
        res = self.rost.getItemByJid(MyJID('amy@wine/work'))
        self.assertEqual(res, items[0])
    
    def test_getGroups(self):
        items = [itemEmul(jid='amy@wine', groups=['1', '4']), 
                 itemEmul(jid='sup@per', groups=['dd',]), 
                 itemEmul(jid='homer@j', groups=['1', 'gs'])]
        self.rost.items = items
        res = self.rost.getGroups()
        groups = ['1', '4', 'dd', 'gs']
        self.assertEqual(res.sort(), groups.sort())
    
    def test_getGroupUsers(self):
        items = [itemEmul(jid='sup@per', groups=['dd',]),
                 itemEmul(jid='amy@wine', groups=['1', '4']), 
                 itemEmul(jid='homer@j', groups=['1', 'gs'])]
        self.rost.items = items
        res = self.rost.getGroupUsers('1')
        self.assertEqual(res.sort(), items[1:].sort())
        res = self.rost.getGroupUsers('dd')
        self.assertEqual(res, items[0:1])
        res = self.rost.getGroupUsers('gs')
        self.assertEqual(res, items[1:2])
        
class TestRosterPresence(unittest.TestCase):
    
    def setUp(self):
        dispatcher.connect(self.got_signal, signal=dispatcher.Any)
        items = [itemEmul('fast@wok'), 
               itemEmul('little@nation', presences={'q':'w', 'r':'t'}), 
               itemEmul('gordon@freeman', presences={'1':'2', '3':'4'})]
        host = hostEmulator(items=items)
        self.rp = roster.RosterPresence(host=host)      
        self.signal = []
        self.sender = []
        self.presence = []
         
    def got_signal(self, signal, sender, presence):
        self.signal.append(signal)
        self.sender.append(sender)
        self.presence.append(presence)
    
    def test_subscribeHandler(self):
        self.rp.subscribeHandler()
        self.assertEqual(self.signal[-1], self.rp.host.subscribe)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
    
    def test_unsubscribeHandler(self):
        self.rp.unsubscribeHandler()
        self.assertEqual(self.signal[-1], self.rp.host.unsubscribe)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
    
    def test_subscribedHandler(self):
        self.rp.subscribedHandler()
        self.assertEqual(self.signal[-1], self.rp.host.subscribed)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
        
    def test_unsubscribedHandler(self):
        self.rp.unsubscribedHandler()
        self.assertEqual(self.signal[-1], self.rp.host.unsubscribed)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
    
    def test_availableHandler(self):
        self.rp.from_=MyJID('fast@wok/home')
        self.rp.availableHandler()
        self.assertEqual(self.signal[-2:], 
                         [self.rp.host.contact_available,
                          self.rp.host.resource_available])
        self.assertEqual(self.sender[-2:], [self.rp.host, self.rp.host])
        self.assertEqual(self.presence[-2:], [self.rp, self.rp])
        
        self.rp.from_=MyJID('fast@wok/home')
        self.rp.availableHandler()
        self.assertEqual(self.signal[-1], 
                         self.rp.host.resource_changed_status)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
        
        n = len(self.signal)
        self.rp.from_=MyJID('gordon@freeman/anywhere')
        self.rp.availableHandler()
        self.assertEqual(self.signal[-1], 
                         self.rp.host.resource_available)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
        self.assertNotEqual(n, len(self.signal))
        
        n = len(self.signal)
        self.rp.from_=MyJID('who@lets.the/dogsout')
        self.rp.availableHandler()          
        self.assertEqual(n, len(self.signal))
    
    def test_unavailableHandler(self):
        self.rp.from_=MyJID('little@nation/q') 
        self.rp.unavailableHandler()
        self.assertEqual(self.rp.host.items[1].presences, {'r':'t'})
        self.assertEqual(self.signal[-1], 
                         self.rp.host.resource_unavailable)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
        
        self.rp.from_=MyJID('little@nation/r')
        self.rp.unavailableHandler()
        self.assertEqual(self.rp.host.items[1].presences, {})
        self.assertEqual(self.signal[-2:], 
                         [self.rp.host.contact_unavailable,
                          self.rp.host.resource_unavailable])
        self.assertEqual(self.sender[-2:], [self.rp.host, self.rp.host])
        self.assertEqual(self.presence[-2:], [self.rp, self.rp])
        
        n = len(self.signal)
        self.rp.from_=MyJID('who@lets.the/dogsout')
        self.rp.unavailableHandler()          
        self.assertEqual(n, len(self.signal))
    
    def test_errorHandler(self):
        self.rp.from_=MyJID('little@nation/q')
        self.rp.errorHandler()
        self.assertEqual(self.rp.host.items[1].presences, {'r':'t'})
        self.assertEqual(self.signal[-1], 
                         self.rp.host.resource_unavailable)
        self.assertEqual(self.sender[-1], self.rp.host)
        self.assertEqual(self.presence[-1], self.rp)
        
        self.rp.from_=MyJID('little@nation/r')
        self.rp.errorHandler()
        self.assertEqual(self.rp.host.items[1].presences, {})
        self.assertEqual(self.signal[-2:], 
                         [self.rp.host.contact_unavailable,
                          self.rp.host.resource_unavailable])
        self.assertEqual(self.sender[-2:], [self.rp.host, self.rp.host])
        self.assertEqual(self.presence[-2:], [self.rp, self.rp])
        
        n = len(self.signal)
        self.rp.from_=MyJID('who@lets.the/dogsout')
        self.rp.errorHandler()          
        self.assertEqual(n, len(self.signal))
