import unittest
from twilix.version import MyVersionQuery
from twilix import errors

class iqEmul(object):
    
    uri=None
    attributes={}
    name='iq' 
    to='some_jid'
    children = []
    
    def makeResult(self):
        return self
        
    def link(self, content):
        self.children.append(content)
    
    def addChild(self, child):
        self.link(shild)


class hostEmul(object):
    def __init__(self):
        self.client_name = 'name'
        self.client_os = 'os'
        self.client_version = 'version'


class MyVersionQueryEmul(MyVersionQuery):
    iq = iqEmul()


class TestVCardQuery(unittest.TestCase):
    
    def setUp(self):
        self.MyVersionQuery = MyVersionQueryEmul()
        self.MyVersionQuery.host = hostEmul()
    
    def test_getHandler(self):
        res = self.MyVersionQuery.getHandler()
        self.asserEqual(res, self.iq)
    
    def test_setHandler(self):
        self.assertRaises(errors.BadRequestException, self.MyVersionQuery.setHandler)
