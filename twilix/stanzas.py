"""
Module discribes stanza-class and basic types of used stanzas. 
There are Message, Presence, Iq classes inherit from Stanza.

Stanzas can be used for incoming stanzas validation and parsing and to
construct your own XML-stanza to be sent into an xmlstream.
"""
import uuid

from twisted.internet.defer import Deferred
from twisted.words.xish.domish import Element

from twilix.base.velement import VElement
from twilix.base.exceptions import ElementParseError,WrongElement
from twilix.errors import Error
from twilix.htmlim import XHtmlIm
from twilix import fields

class Stanza(VElement):
    """
    Extends VElement class from twilix.base.
    Contains fields corresponding to the protocol.

    Base class for all base XMPP Stanzas (iq, message, presence).
    
    Attributes:
        to -- jid attribue 'to'
        
        from\_  -- jid attribue 'from'
        
        type  -- string attribue 'type'
        
        id  -- string attribue 'id'
        
        lang  -- string attribue 'xml:lang'
        
    """
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
        """
        Makes a superclass intialization and set 
        attributes for deferred-style stanzas.
        """
        super(Stanza, self).__init__(*args, **kwargs)
        if 'result_class' in kwargs:
            self._result_class = kwargs['result_class']
        if 'error_class' in kwargs:
            self._error_class = kwargs['error_class']

    def __unicode__(self):
        """Overrrides unicode converter."""
        return self.toXml()

    def __repr__(self):
        """Makes avaliable to show stanza in xml format."""
        return self.toXml()

    def makeError(self, content):
        """
        Creates ErrorStanza from self and then returns it.
        Used to make Error Stanza as reply on any Stanza.
        
        :param content: Error element.
        
        :returns: Error Stanza with Error element.
                
        """
        res = ErrorStanza(to=self.from_, from_=self.to, type_='error',
                          el_name=self.elementName, id=self.id,
                          error=content)
        res.children = self.children + res.children
        return res

    def get_reply(self):
        """
        Creates the reply stanza. 
        There is REPLY_CLASS (if defined) or self-type stanza's class.        
        """
        cls = getattr(self, 'REPLY_CLASS', None) or self.__class__
        return cls(to=self.from_, from_=self.to, type_=self.type_, id=self.id)

class ErrorStanza(Stanza):
    """
    Stanza-inheritor class for any errors.
    Contains fields corresponding to the protocol.
    
    Attributes:
        error -- element node with Error element.
        
    """
    error = fields.ElementNode(Error)
Stanza._error_class = ErrorStanza

class Iq(Stanza):
    """
    Stanza-inheritor class that implements an answer-query type mechanism.
    """
    elementName = 'iq'

    type_ = fields.StringAttr('type')
    id = fields.StringAttr('id')

    def __init__(self, **kwargs):
        """
        Constructor controls for valid value of id,
        calls superclass-constructor and sets deferred 
        attribute for set/get - type queries
        
        """
        if 'id' not in kwargs:
            kwargs['id'] = uuid.uuid4()
        super(Iq, self).__init__(**kwargs)
        if not self.type_ in ('result', 'error') and \
            not kwargs.get('dont_defer', False):
                self.deferred = Deferred()

    def clean_type_(self, value):
        """
        Filters stanzas by type. 
        Used for validation of type\_ field.
        Raises exception for invalid stanzas.
        
        :raises: ElementParseError
        
        """
        if value not in ('set', 'get', 'result', 'error'):
            raise ElementParseError, 'Wrong Iq Type %s' % value
        return value

    def clean_id(self, value):
        """
        Set correct value if id was not found.
        Used for validation of id.    
        """
        if value is None:
            self.addUniqueId()
            return self.id
        return value

    def makeResult(self):
        """Returns result-type Iq stanza"""
        return Iq(to=self.from_, from_=self.to, id=self.id, type_='result',
                  uri=self.uri)

class MyValidator(object):
    """Class for filter stanzas that was sent to myjid."""
    def clean_to(self, v):
        """
        Method raises exception if receiver jid is not host jid.
        
        :raises: WrongElement
        
        """
        if self.dispatcher.myjid != v:
            raise WrongElement
        return v

class MyIq(Iq, MyValidator):
    """Class to filter IQs that was sent to myjid."""
    pass

class Message(Stanza):
    """
    Stanza-inheritor class that implements a message transfer with
    other entities.
    Contains fields corresponding to the protocol.
    
    Attributes:
        body -- string node 'body'
        
        subject  -- string node 'subject'
        
        thread  -- string attribue 'thread'
        
        html  -- element node with XHtmlIm element
        
    """
    elementName = 'message'

    body = fields.StringNode('body', required=False) #?
    subject = fields.StringNode('subject', required=False)
    thread = fields.StringNode('thread', required=False)
    html = fields.ElementNode(XHtmlIm, required=False)

    def clean_type_(self, value):
        """
        Filters stanzas by type. 
        Sets some correct type for invalid stanzas.        
        """
        if not value in ('normal', 'chat', 'groupchat', 'headline', 'error'):
            return 'normal'
        return value

class Presence(Stanza):
    """
    Stanza-inheritor class that implements an entity's presence info.
    Contains fields corresponding to the protocol.
    
    Attributes:
        show -- string node 'show'
        
        status  -- string node 'status'
        
        priority  -- integer attribue 'priority'
                
    """
    elementName = 'presence'

    show = fields.StringNode('show', required=False)
    status = fields.StringNode('status', required=False)
    priority = fields.IntegerNode('priority', required=False)

    def clean_type_(self, value):
        """
        Filters stanzas by type. 
        Sets None type for invalid stanzas.
        
        """
        if not value in ('subscribe', 'subscribed', 'unsubscribe',
                         'unsubscribed', 'available', 'unavailable',
                         'probe', 'error'):
            return None
        return value

    @property
    def type_(self):
        """
        Return type of presence when it's requested. 
        If type is None return 'available'.
        """
        v = self.__getattr__('type_')
        if not v:
            return 'available'
        return v

class Query(VElement):
    """
    VElement-inheritor class. Base for other query-type classes. 
    There is a query part of query-answer mechanism.
    Contains fields corresponding to the protocol.
    
    Attributes:
        node -- string attribute 'node'
        
    """
    elementName = 'query'
    parentClass = Iq

    node = fields.StringAttr('node', required=False)

