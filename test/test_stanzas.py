import unittest

from twilix import stanzas 

class TestStanza(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def testMakeError(self):
        
        stanza = stanzas.Stanza(to='to', from_='from', id='id')
        stanza.elementName = 'stanza'
        res = stanza.makeError('error')
        a = [res.to, res.from_, res.el_name, res.id, res.error]
        b = [stanza.from_, stanza.to, stanza.elementName,
             stanza.id, 'error']
        self.assertEqual(a, b)
