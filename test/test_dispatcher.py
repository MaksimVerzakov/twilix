import unittest
from twilix.dispatcher import Dispatcher

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
    
    def test_dispatch(self):
        
        
        
