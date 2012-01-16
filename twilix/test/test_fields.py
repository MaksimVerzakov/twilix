import unittest

from twilix.fields import AttributeProp, StringType, StringAttr, \
                          JidType, BooleanType, NodeProp
from twilix.jid import internJID
from twilix.base.exceptions import ElementParseError


class ElementEmul(object):
    attributes = {'jack': 'daniels'}    


class TestAttributeProp(unittest.TestCase):
    
    def setUp(self):
        self.ap1 = AttributeProp('jack')
        self.ap2 = AttributeProp('john')
        self.el = ElementEmul()
    
    def test_get_from_el(self):
        res1 = self.ap1.get_from_el(self.el)
        res2 = self.ap2.get_from_el(self.el)
        self.assertEqual(res1, 'daniels')
        self.assertEqual(None, res2)
    
    def test_unicode(self):
        self.assertEqual(u'AttributeProp jack', unicode(self.ap1))
        self.assertEqual(u'AttributeProp john', unicode(self.ap2))


class TestStringType(unittest.TestCase):
    
    def setUp(self):
        self.stype_req = StringType()
        self.stype_req.required = True
        self.stype_not_req = StringType()
        self.stype_not_req.required = False
        
    def test_clear(self):
        str = 'hello'
        self.assertEqual(self.stype_req.clean(str), unicode(str))
        self.assertEqual(self.stype_not_req.clean(None), None)
        self.assertRaises(ElementParseError, self.stype_req.clean, None)

class TestStringAttr(unittest.TestCase):
    
    def test_clean_set(self):
        str = 'hello'
        self.assertEqual(StringAttr('any').clean_set(str), unicode(str))
        self.assertEqual(StringAttr('any').clean_set(None), None)
     
        
class TestJidType(unittest.TestCase):
    
    def test_topython(self):
        jid = 'highway@hell'
        jt = JidType()
        self.assertEqual(internJID(jid), jt.to_python(jid))
        self.assertEqual(None, jt.to_python(None))

class TestBooleanType(unittest.TestCase):
    
    def setUp(self):
        self.bt = BooleanType()        
    
    def test_topython(self):
        self.assertTrue(self.bt.to_python('true'))
        self.assertFalse(self.bt.to_python(None))
        self.assertFalse(self.bt.to_python('any'))
    
    def test_clean_set(self):
        self.assertEqual('true', self.bt.clean_set('any'))
        self.assertEqual('false', self.bt.clean_set(None))       
