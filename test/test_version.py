import unittest

from twilix.version import MyVersionQuery
from twilix import errors

from twilix.test import iqEmul, hostEmul


class MyVersionQueryEmul(MyVersionQuery):
    iq = iqEmul()


class TestVCardQuery(unittest.TestCase):
    
    def setUp(self):
        self.MyVersionQuery = MyVersionQueryEmul()
        self.MyVersionQuery.host = hostEmul(client_name = 'name', 
                                            client_os = 'os',
                                            client_version = 'version')
    
    def test_getHandler(self):
        res = self.MyVersionQuery.getHandler()
        self.asserEqual(res, self.iq)
    
    def test_setHandler(self):
        self.assertRaises(errors.BadRequestException, self.MyVersionQuery.setHandler)
