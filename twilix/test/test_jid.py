import unittest

from twisted.words.protocols.jabber.jid import JID
from twilix import jid
    
    
class TestMyJID(unittest.TestCase):
    
    def setUp(self):
        self.name = u'name'
        self.host = u'host'
        self.res = u'resource'
        
        #import pdb; pdb.set_trace()
        self.jid = jid.MyJID(tuple=(self.name, self.host, self.res))
        self.bare_jid = jid.MyJID(tuple=(self.name, self.host, None))
        
            
    def test_is_bare(self):
        self.assertEqual(self.jid.is_bare, False)
        self.assertEqual(self.bare_jid.is_bare, True)

    def test_bare(self):
        self.assertEqual(self.jid.bare(), 
                         JID(tuple=(self.name, self.host, None)))
        self.assertEqual(self.bare_jid.bare(), 
                         JID(tuple=(self.name, self.host, None)))
    
    def test_unicode(self):
        self.assertEqual(self.jid.__unicode__(), 
                         u'%s@%s/%s' % (self.name, self.host, self.res))
        self.assertEqual(self.bare_jid.__unicode__(), 
                         u'%s@%s' % (self.name, self.host))
    
class TestInternJID(unittest.TestCase):
    
    def test_internJID(self):
        jidstring = 'user@host/resuorce'
        test_jid = JID(jidstring)
        self.assertEqual(jid.internJID(jidstring), test_jid)
        self.assertEqual(jid.internJID(jidstring), test_jid)
