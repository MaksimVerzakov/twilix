import unittest

import twilix.fields

class elementEmul(object):
    def __init__(self, attr_name, attr_value):
        self.attributes[attr_name] = attr_value

class TestAttributeProp(unittest.TestCase):
    
    def test_get_from_el(self):
        pass
        #el = elementEmul('xmlattr', 'value')
        #attr = fields.AttributeProp('xmlattr')
        #attr.get_from_el(el)
        
