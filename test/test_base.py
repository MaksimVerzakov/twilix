import unittest

from twilix.base.myelement import MyElement
from twilix.base.velement import VElement

class TestBase(unittest.TestCase):
    
    def setUp(self):
        self.seq = range(10)
