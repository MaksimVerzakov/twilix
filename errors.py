"""Describe all expected classes of errors."""
import string
import sys

from twilix.base import VElement, MyElement
from twilix import fields

conditions = {
    'bad-request': 'modify',
    'conflict': 'cancel',
    'feature-not-implemented': 'cancel',
    'forbidden': 'auth',
    'gone': 'modify',
    'internal-server-error': 'wait',
    'item-not-found': 'cancel',
    'jid-malformed': 'modify',
    'not-acceptable': 'modify',
    'not-allowed': 'cancel',
    'not-authorized': 'auth',
    'payment-required': 'auth',
    'recepient-unavailable': 'wait',
    'redirect': 'modify',
    'registration-required': 'auth',
    'remote-server-not-found': 'cancel',
    'remote-server-timeout': 'wait',
    'resource-constraint': 'wait',
    'service-unavailable': 'cancel',
    'subscription-required': 'auth',
    'undefined-condition': 'Undefined condition',
    'unexpected-request': 'wait',
}

module = sys.modules[__name__]
def condition_to_name(condition):
    """
    Bring condition to CapWords style.
    :returns:
        condition in CapWords style.
    """
    words = condition.split('-')
    words = map(string.capitalize, words)
    return ''.join(words)

def exception_by_condition(condition): 
    """Return exception appropriate to condition."""
    exc = getattr(module, '%sException' % condition_to_name(condition.name))
    return exc(condition.content, conditions[condition.name])

class ExceptionWithType(Exception):
    """Extends class ExceptionWithContent. Define type field."""
    def __init__(self, type=None, reason=None, *args, **kwargs):
        self.reason = reason
        self.type = type
        if self.type == None:
            self.type =  conditions[self.condition]
        self.content = Error(condition=self.condition,
                             text=self.reason,
                             type_=self.type)
        super(ExceptionWithType, self).__init__(*args, **kwargs)

for condition in conditions:
    """Defining exception for all possible conditions."""
    class DummyException(ExceptionWithType):
        pass
    name = '%sException' % condition_to_name(condition)
    DummyException.__name__ = name
    DummyException.condition = condition
    setattr(module, name, DummyException)

class ConditionNode(fields.ElementNode):
    """
    Extends ElementNode from twilix.fields.
    Contains Condition element.
    """
    def clean(self, value):
        return value
    def clean_set(self, value):
        return MyElement((self.cls.elementUri, value))

class Condition(VElement):
    """
    Extends VElement from twilix.base.
    Contains condition value.
    """
    elementUri = 'urn:ietf:params:xml:ns:xmpp-stanzas'

class Error(VElement):
    """
    Extends VElement from twilix.base.
    Contains string attribute type, condition node and text node.    
    """
    elementName = 'error'

    type_ = fields.StringAttr('type')
    condition = ConditionNode(Condition)
    text = fields.StringNode('text', required=False,
                             uri='urn:ietf:params:xml:ns:xmpp-stanzas')

    def clean_type_(self, value):
        """
        Cut off errors with wrong type.
        :returns:
            value if it has correct type.
        :raises:
            ElementParseError if value has a wrong type.
        """
        if value not in ('cancel', 'continue', 'modify', 'auth', 'wait'):
            raise ElementParseError, 'Wrong Error Type %s' % value
        return value
