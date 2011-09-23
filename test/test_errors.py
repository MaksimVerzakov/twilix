import unittest

from twilix import errors, base
#from twilix.test import dispatcherEmul, hostEmul

class tmp(object):
    elementName = 'FakeClass'

    
class TestConditionNode(unittest.TestCase):
    
    def test_clean(self):
        condition = errors.ConditionNode(tmp())
        value = 'anything'
        self.assertEqual(condition.clean(value), value)


class TestUndefinedConditionException(unittest.TestCase):
    
    def test_init(self):
        i = errors.UndefinedConditionException('>:4 8 15 16 23 42', type='modify')


class TestError(unittest.TestCase):
    
    def test_clean_type_(self):
        error = errors.Error(type_='get', to='jid', from_='some_jid',
                             condition='any')
        value = 'anything'
        self.assertEqual(condition.clean(value), value)   

    def test_clean_type_(self):
        error = errors.Error(type_='get', to='jid', from_='some_jid',
                             condition='any')
        self.assertRaises(base.ElementParseError, error.clean_type_, 'something')
        values = ('cancel', 'continue', 'modify', 'auth', 'wait')
        for value in values:
            self.assertEqual(error.clean_type_(value), value)
