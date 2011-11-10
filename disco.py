"""Contains classes that implement service discovery. (XEP-0030)

You can use it to get disco items or info from another jabber entities and to
represent your own items and feature to others."""
import hashlib
import base64

from twilix.base.velement import VElement
from twilix.stanzas import Query, Iq, MyIq
from twilix.jid import internJID
from twilix import fields, errors

class CapsElement(VElement): #XXX: invate automatize caps calculation
    """
    Extends VElement. 
    Describe node for entity capabilities with fields that corresponds 
    to the protocol.
    
    Attributes:
        hash\_ - string attribute contains features hash type
        
        node -- string attribute contains caps node
        
        ver -- string attribute contains features hash
       
    """
    elementName = 'c'
    elementUri = 'http://jabber.org/protocol/caps'

    hash_ = fields.StringAttr('hash')
    node = fields.StringAttr('node')
    ver = fields.StringAttr('ver')

class Identity(VElement):
    """
    Extends VElement. 
    Describe node for identity with fields that corresponds to the
    protocol.
    
    Attributes:
        category -- string attribute
        
        type\_ -- string attribute
        
        iname -- string attribute contains human readable name

    See: http://xmpp.org/registrar/disco-categories.html
            
    """
    elementName = 'identity'
    
    category = fields.StringAttr('category')
    type_ = fields.StringAttr('type')
    iname = fields.StringAttr('name', required=False)

class Feature(VElement):
    """
    Extends VElement. 
    Describes node for feature with field that corresponds to the
    protocol.
    
    Attributes:
        var -- string attribute with a feature namespace
                 
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
        Return result iq when dispatcher gets get Disco Info query.
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
    Describe base discovery item element with fields that corresponds 
    to the protocol.
    
    Attributes:
        jid -- jid attribute
        
        iname -- string attribute contains human readable name
        
        node -- string attribute
                 
    """
    elementName = 'item'

    jid = fields.JidAttr('jid')
    iname = fields.StringAttr('name', required=False)
    node = fields.StringAttr('node', required=False)

class DiscoItemsQuery(Query):
    """
    Extends Query class.
    
    Attibutes:
        items -- element node with DiscoItem
        
        node -- string attribute 'node'
            
    """
    elementUri = 'http://jabber.org/protocol/disco#items'

    items = fields.ElementNode(DiscoItem, required=False, listed=True,
                               unique=True)
    node = fields.StringAttr('node', required=False)

class VDiscoItemsQuery(DiscoItemsQuery):
    """
    Extends DiscoItemsQuery.
    Set MyIq as parent class.
    Describe get handler for disco items query.
    """
    parentClass = MyIq
    def getHandler(self):
        """
        Return result iq when dispatcher gets Disco Items query.
        """
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
        """Raise ItemNotFoundException in any case."""
        raise errors.ItemNotFoundException()        

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
    """Describe interaction dispatcher with service discovery.

       You can set your info or items using attributes static_info and
       static_items which are a dictionaries keys of which are nodes and
       values are instances of DiscoInfoQuery or DiscoItemsQuery appropriately

       For the root node you should use attributes root_info and root_items in
       the same way.

       To implement some dynamic nodes you should use handler param for the
       init method where you can pass your own Disco handlers which will
       generate any answers in runtime based on your criterias.

       :param dispatcher: dispatcher instance to use with the service."""

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
        Initialize the service (Register all necessary handlers and add service
        discovery features as own. When called, the entity will be able to
        answer disco queries.

        :param handlers: any extra disco handlers to handle dynamic disco nodes
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
        Get disco items from another entity.
        Return deferred object with the result of type DiscoItemsQuery.

        :param jid: JID of the entity to get items from.

        :param node: node name to get items from.

        :param from_: set some specific from address. Uses myjid if none given.
        
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
        Get disco info from another entity.
        Return deferred object with the result of type DiscoInfoQuery.

        :param jid: JID of the entity to get items from.

        :param node: node name to get items from.

        :param from_: set some specific from address. Uses myjid if none given.
        
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
        """
        Calculate and return hash of identities and features in base64 format 
        based on own identities and features.
        """
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
