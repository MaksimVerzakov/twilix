import unittest

from twilix import fields

class TestAttributeProp(unittest.TestCase):
    
    def setUp(self): 
        self.attr = fields.AttributeProp('some')    

    def test_get_from_el(self):
        element = fields.AttributeProp('some')    
        self.attr.get_from_el(element)
