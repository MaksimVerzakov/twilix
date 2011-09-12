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
    'unexpected-request': 'wait',
}

module = sys.modules[__name__]
def condition_to_name(condition):
    """
    Bring condition to CapWords style.
    Used to define standart exception from rfc 3920.
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
    """
    Extends class Exception. Define type and reason fields.
    Base class for special exceptions.
    """
    def __init__(self, type=None, reason=None, *args, **kwargs):
        self.reason = reason
        self.type = type
        if self.type == None:
            self.type =  conditions[self.condition]
        super(ExceptionWithType, self).__init__(*args, **kwargs)

class ExceptionWithContent(ExceptionWithType):
    """
    Extends class ExceptionWithType. 
    Contains content field - Error element.
    """
    def __init__(self, *args, **kwargs):
        super(ExceptionWithContent, self).__init__(*args, **kwargs)
        self.content = Error(condition=self.condition,
                             text=self.reason,
                             type_=self.type)

class ExceptionWithAppCondition(ExceptionWithType):
    """
    Extends class ExceptionWithType.
    Used to describe undefined exception with special application 
    description of error.
    Contains content field - Application Error element.
    """
    def __init__(self, app_condition, *args, **kwargs):
        super(ExceptionWithAppCondition, self).__init__(*args, **kwargs)
        self.app_condition = app_condition
        self.content = AppError(condition=self.condition,
                                text=self.reason,
                                type_=self.type,
                                app_text=self.app_condition)
    
for condition in conditions:
    """Defining exception for all possible conditions."""
    class DummyException(ExceptionWithContent):
        pass
    name = '%sException' % condition_to_name(condition)
    DummyException.__name__ = name
    DummyException.condition = condition
    setattr(module, name, DummyException)

class UndefinedConditionException(ExceptionWithAppCondition):
    """Describe undefined condition."""
    condition = 'undefined-condition'

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
    Contains string attribute type, condition node and text node as
    described in rfc 3920. 
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

class AppError(Error):
    """
    Extends class Error.
    Contains String Node for special application condition as described 
    in rfc 3920.    
    """
    app_text = fields.StringNode('text', required=False,
                                 uri='application-ns')
