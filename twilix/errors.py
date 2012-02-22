"""Describe all expected classes of errors.

This module is a wrapper for an XMPP error stanzas to Python's exceptions and
vice-versa.

When you want to answer with an error in your handler you can just raise an
exception like this: ::

    raise NotAllowedError, "Use another condition"

When you want to check if some request returns an error you can just catch
an exception like any other Python exception::

    try:
        version = yield self.version.getVersion('example.net')
    except FeatureNotImplementedError:
        sys.stderr.write('example.net does not support version request')

"""
import string
import sys

from twilix.base.velement import VElement
from twilix.base.myelement import MyElement
from twilix.base.exceptions import ElementParseError
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

errorCodeMap = {                                         
    "bad-request": 400,
    "conflict": 409,
    "feature-not-implemented": 501,
    "forbidden": 403,
    "gone": 302,
    "internal-server-error": 500,
    "item-not-found": 404,
    "jid-malformed": 400,
    "not-acceptable": 406,
    "not-allowed": 405,
    "not-authorized": 401,
    "payment-required": 402,
    "recipient-unavailable": 404,
    "redirect": 302,
    "registration-required": 407,
    "remote-server-not-found": 404,
    "remote-server-timeout": 504,
    "resource-constraint": 500,
    "service-unavailable": 503,
    "subscription-required": 407,
    "undefined-condition": 500,
    "unexpected-request": 400
}

module = sys.modules[__name__]
def condition_to_name(condition):
    """
    Bring condition to CapWords style.
    Used to define standart exception from the RFC-3920.
    
    :returns: condition in CapWords style.
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
    def __init__(self, reason=None, type=None, *args, **kwargs):
        self.reason = reason
        self.type = type
        if self.type == None:
            self.type = conditions[self.condition]
        super(ExceptionWithType, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.reason

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

    def __unicode__(self):
        text = u''
        if self.content.text:
            text = u', text: %s' % (self.content.text,)
        return u'<XMPP %s%s, type: %s>' % (
                self.__class__.__name__,
                text,
                self.content.type_)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return str(self.__unicode__())

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
    def to_python(self, value):
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
    Contains fields corresponding to the rfc 3920. 
    
    Attributes:
        type\_ -- string attribute 'type'
        
        condition -- condition node with Condition
        
        text -- string node 'text'
        
    """
    elementName = 'error'

    type_ = fields.StringAttr('type')
    condition = ConditionNode(Condition)
    text = fields.StringNode('text', required=False,
                             uri='urn:ietf:params:xml:ns:xmpp-stanzas')

    def clean_type_(self, value):
        """
        Cut off errors with wrong type.
        Used for validaion.
        
        :returns: value if it has correct type.
        
        :raises: ElementParseError if value has a wrong type.
        
        """
        if value not in ('cancel', 'continue', 'modify', 'auth', 'wait'):
            raise ElementParseError, 'Wrong Error Type %s' % value
        return value

class AppError(Error):
    """
    Extends class Error.
    Contains field corresponding to the RFC-3920.
    
    Attributes:
        app_text -- string node 'text'
    """
    app_text = fields.StringNode('text', required=False,
                                 uri='application-ns')
