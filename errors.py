import string
import sys

from twilix.base import VElement, MyElement
from twilix import fields

conditions = {
    'bad-request': 'Bad request',
    'conflict': 'Conflict',
    'feature-not-implemented': 'Feature not implemented',
    'forbidden': 'Forbidden',
    'gone': 'Gone',
    'internal-server-error': 'Internal server error',
    'item-not-found': 'Item not found',
    'jid-malformed': 'JID malformed',
    'not-acceptable': 'Not acceptable',
    'not-allowed': 'Not allowed',
    'not-authorized': 'Not authorized',
    'payment-required': 'Payment required',
    'recepient-unavailable': 'Recepient unavalable',
    'redirect': 'Redirect',
    'registration-required': 'Registration required',
    'remote-server-not-found': 'Remote server not found',
    'remote-server-timeout': 'Remote server timeout',
    'resource-constraint': 'Resource constraint',
    'service-unavailable': 'Service unavalable',
    'subscription-required': 'Subscription required',
    'undefined-condition': 'Undefined condition',
    'unexpected-request': 'Unexpected request',
}

module = sys.modules[__name__]
def condition_to_name(condition):
    words = condition.split('-')
    words = map(string.capitalize, words)
    return ''.join(words)

def exception_by_condition(condition):
    exc = getattr(module, '%sException' % condition_to_name(condition.name))
    return exc(condition.content, conditions[condition.name])

class ExceptionWithReason(Exception):
    def __init__(self, reason, *args, **kwargs):
        self.reason = reason
        super(ExceptionWithReason, self).__init__(*args, **kwargs)

class ExceptionWithContent(ExceptionWithReason):
    def __init__(self, content, *args, **kwargs):
        self.content = content
        super(ExceptionWithContent, self).__init__(*args, **kwargs)

for condition in conditions:
    reason = conditions[condition]
    class DummyException(ExceptionWithContent):
        pass
    name = '%sException' % condition_to_name(condition)
    DummyException.__name__ = name
    setattr(module, name, DummyException)

class ConditionNode(fields.ElementNode):
    def clean(self, value):
        return value
    def clean_set(self, value):
        return MyElement((self.cls.elementUri, value))

class Condition(VElement):
    elementUri = 'urn:ietf:params:xml:ns:xmpp-stanzas'

class Error(VElement):
    elementName = 'error'

    type_ = fields.StringAttr('type')
    condition = ConditionNode(Condition)
    text = fields.StringNode('text', required=False,
                             uri='urn:ietf:params:xml:ns:xmpp-stanzas')

    def clean_type_(self, value):
        if value not in ('cancel', 'continue', 'modify', 'auth', 'wait'):
            raise ElementParseError, 'Wrong Error Type %s' % value
        return value
