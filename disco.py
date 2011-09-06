"""Contains classes that realize service discovery."""
import hashlib
import base64

from twilix.base import WrongElement, VElement
from twilix.stanzas import Query, Iq, MyIq
from twilix.jid import internJID
from twilix import fields

class CapsElement(VElement):
    """
    Extends VElement. 
    Describe node for entity capabilities.     
    """
    elementName = 'c'
    elementUri = 'http://jabber.org/protocol/caps'

    hash_ = fields.StringAttr('hash')
    node = fields.StringAttr('node')
    ver = fields.StringAttr('ver')

class Identity(VElement):
    """
    Extends VElement. 
    Describe node for identity.     
    """
    elementName = 'identity'
    
    category = fields.StringAttr('category')
    type_ = fields.StringAttr('type')
    iname = fields.StringAttr('name', required=False)

class Feature(VElement):
    """
    Extends VElement. 
    Describe node for feature.     
    """
    elementName = 'feature'

    var = fields.StringAttr('var')

class DiscoInfoQuery(Query):
    """
    Extends Query class.
    Contains information about features and identities.
    """
    elementUri = 'http://jabber.org/protocol/disco#info'
    
    identities = fields.ElementNode(Identity, required=False,
                                    listed=True, unique=True)
    features = fields.ElementNode(Feature, required=False,
                                  listed=True, unique=True)
    node = fields.StringAttr('node', required=False)

class VDiscoInfoQuery(DiscoInfoQuery):
    """
    Extends class DiscoInfoQuery.
    Set MyIq as parent class. 
    Describe get handler.
    """
    parentClass = MyIq
    def getHandler(self):
        """
        
        """
        node = self.node or ''
        info_query = None
        if self.host.static_info.has_key(node):
            info_query = self.host.static_info[node]
            info_query.node = self.node
        if info_query is None:
            return
        iq = self.iq.makeResult()
        iq.link(info_query)
        return iq

class DiscoItem(VElement):
    """
    Extends VElement.
    Describe base discovery item. 
    Contains fields for jid, name and node.
    """
    elementName = 'item'

    jid = fields.JidAttr('jid')
    iname = fields.StringAttr('name', required=False)
    node = fields.StringAttr('node', required=False)

class DiscoItemsQuery(Query):
    """
    
    """
    elementUri = 'http://jabber.org/protocol/disco#items'

    items = fields.ElementNode(DiscoItem, required=False, listed=True,
                               unique=True)
    node = fields.StringAttr('node', required=False)

class VDiscoItemsQuery(DiscoItemsQuery):
    parentClass = MyIq
    def getHandler(self):
        node = self.node or ''
        items_query = None
        if self.host.static_info.has_key(node):
            items_query = self.host.static_items[node]
            items_query.node = self.node
        if items_query is None:
            return
        iq = self.iq.makeResult()
        iq.link(items_query)
        return iq

class NotFoundQuery(object):
    """Contains handler for making error if item isn't found."""
    parentClass = MyIq
    def anyHandler(self):
        return self.iq.makeError('cancel', 'item-not-found')

class NotFoundDiscoItemsQuery(NotFoundQuery, DiscoItemsQuery):
    """
    Inherit NotFoundQuery and DiscoItemsQuery.
    Handler for cases when disco item isn't found.
    """
    pass

class NotFoundDiscoInfoQuery(NotFoundQuery, DiscoInfoQuery):
    """
    Inherit NotFoundQuery and DiscoItemsQuery.
    Handler for cases when disco info isn't found.
    """
    pass

class Disco(object):
    """Describe interaction with service discovery."""
    def __init__(self, dispatcher):
        """
        Initialize class. 
        Set dispatcher and base fields.
        """
        self.dispatcher = dispatcher

        self.static_info = {'': DiscoInfoQuery()}
        self.static_items = {'': DiscoItemsQuery()}
        self.root_info = self.static_info['']
        self.root_items = self.static_items['']

    def init(self, handlers=None):
        """
        Register VDiscoInfoQuery, VDiscoItemsQuery, 
        NotFoundDiscoInfoQuery, NotFoundDiscoItemsQuery as handlers.
        Register other handlers if argument handlers isn't None.
        Add features to self.root_info.
        """
        if handlers is None:
            handlers = ()
        self.dispatcher.registerHandler((VDiscoInfoQuery, self))
        self.dispatcher.registerHandler((VDiscoItemsQuery, self))
        for handler, host in handlers:
            self.dispatcher.registerHandler((handler, host))
        self.dispatcher.registerHandler((NotFoundDiscoInfoQuery, self))
        self.dispatcher.registerHandler((NotFoundDiscoItemsQuery, self))

        features = (
                    Feature(var='http://jabber.org/protocol/disco#items'),
                    Feature(var='http://jabber.org/protocol/disco#info'),
                   )
        self.root_info.addFeatures(features)

    def getItems(self, jid, node=None, from_=None):
        """
        Send get iq with DiscoItemsQuery as child to dispatcher.
        Return deferred object with the result.
        :returns:
            query.iq.deferred - deferrer object with result or error.
        """
        if from_ is None:
            from_ = self.dispatcher.myjid
        query = DiscoItemsQuery(host=self, node=node,
                                parent=Iq(type_='get', to=jid, from_=from_))
        query.iq.result_class = DiscoItemsQuery
        self.dispatcher.send(query.iq)
        return query.iq.deferred

    def getInfo(self, jid, node=None, from_=None):
        """
        Send get iq with DiscoInfoQuery as child to dispatcher.
        Return deferred object with the result.
        :returns:
            query.iq.deferred - deferrer object with result or error.
        """
        if from_ is None:
            from_ = self.dispatcher.myjid
        query = DiscoInfoQuery(host=self, node=node,
                               parent=Iq(type_='get', to=jid, from_=from_))
        query.iq.result_class = DiscoInfoQuery
        self.dispatcher.send(query.iq)
        return query.iq.deferred

    def getCapsHash(self):
        s = u''
        info = self.root_info
        for i in info.identities: #XXX: add identities sort
            s += '%s/%s//%s<' % (i.category, i.type_, i.iname)
        features = []
        for f in info.features:
            features.append(f.var)
        features.sort()
        for f in features:
            s += '%s<' % f
        s = s.encode('utf-8')
        return base64.b64encode(hashlib.sha1(s).digest())
