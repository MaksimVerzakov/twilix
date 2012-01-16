import unittest

from twilix.dispatcher import Dispatcher
from twilix.stanzas import Iq
from twilix import fields
from twilix.base.exceptions import WrongElement, ElementParseError

class xmlEmul(object):
    def send(self, data):
        self.data = data
    def addObserver(self, name, dispatcher):
        pass
        
        
class TestDispatcher(unittest.TestCase):
    
    def setUp(self):
        self.dispatcher = Dispatcher(xmlEmul(), myjid='john@server.org')
    
    def test_registerHandler(self):
        res = self.dispatcher.registerHandler('handler')
        self.assertTrue(res)
        res = self.dispatcher.registerHandler('handler')
        self.assertEqual(res, None)
        
    def test_unregisterHandler(self):
        res = self.dispatcher.registerHandler('handler')
        res = self.dispatcher.unregisterHandler('handler')
        self.assertTrue(res)
        res = self.dispatcher.unregisterHandler('handler')
        self.assertEqual(res, None)
    
    def test_registerHook(self):
        res = self.dispatcher.registerHook('hook_name', 'hook')
        self.assertEqual(res, True)
        res = self.dispatcher.registerHook('hook_name', 'hook')
        self.assertEqual(res, None)
    
    def test_unregisterHook(self):
        res = self.dispatcher.registerHook('hook_name', 'hook')
        res = self.dispatcher.unregisterHook('hook_name', 'hook')
        self.assertEqual(res, True)
        res = self.dispatcher.unregisterHook('hook_name', 'hook')
        self.assertEqual(res, None)
    
    def test_getHooks(self):
        self.dispatcher.registerHook('hook_name', 'hook1')
        self.dispatcher.registerHook('hook_name', 'hook2')
        self.dispatcher.registerHook('hook_name', 'hook3')
        l = ['hook1', 'hook2', 'hook3']
        self.assertEqual(self.dispatcher.getHooks('hook_name'), l)

    def test_send(self):
        # XXX: implement
        pass
    
    def test_dispatch(self):
        # XXX: implement
        pass
        
        
