import unittest

from twilix import stanzas, base
from twilix.test import dispatcherEmul, hostEmul

class TestStanza(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def testMakeError(self):
        pass
     #   stanza = stanzas.Stanza(to='to', from_='from', id='id')
     #   stanza.elementName = 'stanza'
     #   res = stanza.makeError('error')
     #   a = [res.to, res.from_, res.el_name, res.id, res.error]
     #   b = [stanza.from_, stanza.to, stanza.elementName,
     #        stanza.id, 'error']
     #   self.assertEqual(a, b)

class TestIq(unittest.TestCase):
    
    def test_clean_type_(self):
        iq = stanzas.Iq(type_='get', to='jid', from_='some_jid')
        self.assertRaises(base.ElementParseError, iq.clean_type_, 'something')
        values = ['set', 'get', 'result', 'error']
        for value in values:
            self.assertEqual(iq.clean_type_(value), value)
    
    def test_clean_id(self):
        iq = stanzas.Iq(type_='get', to='jid', from_='some_jid')
        value = 'id'
        self.assertEqual(iq.clean_id(value), value)
        self.assertEqual(iq.clean_id(None), 'H_1')
    
    def test_makeResult(self):
        pass
        #self.Iq = stanzas.Iq(type_='get', to='jid', from_='some_jid')
        #res = self.Iq.makeResult()
        #iq = Iq(to=self.iq.from_, from_=self.iq.to, id=self.iq.id,
        #        type_='result', uri=self.iq.uri)
        #self.assertEqual(res, iq)
        
class TestMyValidator(unittest.TestCase):
    def test_clean_to(self):
        Validator = stanzas.MyValidator()
        disp = dispatcherEmul('myjid')
        Validator.host = hostEmul(dispatcher=disp)
        self.assertEqual(Validator.clean_to('myjid'), disp.myjid)
        self.assertRaises(base.WrongElement, Validator.clean_to, 'some_jid')

class TestMessage(unittest.TestCase):
    
    def test_clean_type_(self):
        msg = stanzas.Message(to='jid', from_='some_jid')
        self.assertEqual(msg.clean_type_('something'), 'normal')
        values = ('normal', 'chat', 'groupchat', 'headline', 'error')
        for value in values:
            self.assertEqual(msg.clean_type_(value), value)

class TestPresence(unittest.TestCase):
    
    def test_clean_type_(self):
        prs = stanzas.Presence(to='jid', from_='some_jid')
        self.assertEqual(prs.clean_type_('something'), None)
        values = ('subscribe', 'subscribed', 'unsubscribe',
                  'unsubscribed', 'available', 'unavailable',
                  'probe', 'error')
        for value in values:
            self.assertEqual(prs.clean_type_(value), value)

