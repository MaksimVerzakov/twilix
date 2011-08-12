from twisted.internet.defer import Deferred
from twisted.words.xish.domish import Element

from twilix.base import WrongElement, ElementParseError, VElement
from twilix.errors import Error
from twilix.htmlim import XHtmlIm
from twilix import fields

class Stanza(VElement):
    elementUri = (
                  'jabber:client',
                  'jabber:server',
                  'jabber:component:accept',
                  None,
                 )

    to = fields.JidAttr('to', required=False)
    from_ = fields.JidAttr('from', required=False)
    type_ = fields.StringAttr('type', required=False)
    id = fields.StringAttr('id', required=False)
    lang = fields.StringAttr('xml:lang', required=False)

    def __init__(self, *args, **kwargs):
        super(Stanza, self).__init__(*args, **kwargs)
        self.result_class = kwargs.get('result_class', None)
        self.error_class = kwargs.get('error_class', ErrorStanza)

    def __unicode__(self):
        return self.toXml()

    def __repr__(self):
        return self.toXml()

    def makeError(self, etype, condition, description=None):
        res = ErrorStanza(to=self.from_, from_=self.to, type_='error',
                          el_name=self.elementName, id=self.id,
                          error=Error(condition=condition,
                                      text=description,
                                      type_=etype))
        res.children = self.children + res.children
        return res

    def get_reply(self):
        cls = getattr(self, 'REPLY_CLASS', None) or self.__class__
        return cls(to=self.from_, from_=self.to, type_=self.type_, id=self.id)

class ErrorStanza(Stanza):
    error = fields.ElementNode(Error)

class Iq(Stanza):
    elementName = 'iq'

    type_ = fields.StringAttr('type')
    id = fields.StringAttr('id')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = 'H_%s' % Element._idCounter
            Element._idCounter += 1
        super(Iq, self).__init__(**kwargs)
        if not self.type_ in ('result', 'error') and \
            not kwargs.get('dont_defer', False):
                self.deferred = Deferred()
                #from twisted.internet import reactor
                #from twisted.internet.defer import timeout
                #self.timeoutCall = reactor.callLater(
                #    60,
                #    lambda: self.deferred.called or \
                #            timeout(self.deferred))

    def clean_type_(self, value):
        if value not in ('set', 'get', 'result', 'error'):
            raise ElementParseError, 'Wrong Iq Type %s' % value
        return value

    def clean_id(self, value):
        if value is None:
            self.addUniqueId()
            return self.id
        return value

    def makeResult(self):
        return Iq(to=self.from_, from_=self.to, id=self.id, type_='result',
                  uri=self.uri)

class MyValidator(object):
    def clean_to(self, v):
        if self.host and self.host.dispatcher.myjid != v:
            raise WrongElement
        return v

class MyIq(Iq, MyValidator):
    pass

class Message(Stanza):
    elementName = 'message'

    body = fields.StringNode('body', required=False) #?
    subject = fields.StringNode('subject', required=False)
    thread = fields.StringNode('thread', required=False)
    html = fields.ElementNode(XHtmlIm, required=False)

    def clean_type_(self, value):
        if not value in ('normal', 'chat', 'groupchat', 'headline', 'error'):
            return 'normal'
        return value

class Presence(Stanza):
    elementName = 'presence'

    show = fields.StringNode('show', required=False)
    status = fields.StringNode('status', required=False)
    priority = fields.IntegerNode('priority', required=False)

    def clean_type_(self, value):
        if not value in ('subscribe', 'subscribed', 'unsubscribe',
                         'unsubscribed', 'available', 'unavailable',
                         'probe', 'error'):
            return None
        return value

    @property
    def type_(self):
        v = self.__getattr__('type_')
        if not v:
            return 'available'
        return v

class Query(VElement):
    elementName = 'query'
    parentClass = Iq

    node = fields.StringAttr('node', required=False)

    def __init__(self, *args, **kwargs):
        self._iq = None
        super(Query, self).__init__(*args, **kwargs)

    @classmethod
    def createFromElement(cls, el, host=None, dont_defer=False):
        parent = cls.parentClass.createFromElement(el, host=host,
                                                   dont_defer=dont_defer)
        el = parent.firstChildElement()
        if el is None:
            raise WrongElement
        if el.uri != cls.elementUri or el.name != cls.elementName:
            raise WrongElement
        if parent.type_ == 'result' and el is None:
            raise WrongElement
        query = super(Query, cls).createFromElement(el, host=host)
        query.parent = parent
        query.children = el.children
        return query

    @property
    def iq(self):
        if self._iq is None:
            self._iq = self.topElement()
        return self._iq

