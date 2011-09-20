import unittest

from twilix.base import MyElement, VElement

class TestBase(unittest.TestCase):
    
    def setUp(self):
        self.seq = range(10)
