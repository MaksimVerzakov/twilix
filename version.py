"""
Module implements jabber:iq:version feature
"""

from twilix.stanzas import Query, MyIq, Iq
from twilix.disco import Feature
from twilix import fields

class VersionQuery(Query):
    """
    Base class for version queries
    """
    elementUri = 'jabber:iq:version'
    
    client_name = fields.StringNode('name', required=False)
    client_version = fields.StringNode('version', required=False)
    client_os = fields.StringNode('os', required=False)

class MyVersionQuery(VersionQuery):
    """
    Class handler for set/get version queries
    """
    parentClass = MyIq

    def getHandler(self):
        """
        Calls from dispatcher when there is get version query.
        
        Returns iq stanza with version's info.
        """
        iq = self.iq.makeResult()
        query = VersionQuery(client_name=self.host.client_name,
                             client_version=self.host.client_version,
                             client_os=self.host.client_os,
                             parent=iq)
        return iq

    def setHandler(self):
        """
        Calls from dispatcher when there is set version query.
        
        There is incorrect query. Method returns error stanza.
        """
        return self.iq.makeError('cancel', 'bad-request')

class ClientVersion(object):
    """
    Class for linking with host, dispatcher and query-handlers objects
    """
    
    def __init__(self, dispatcher, client_name=None, client_version=None,
                 client_os=None):
        """Sets version info and dispatcher value"""
        self.dispatcher = dispatcher
        self.client_name = client_name
        self.client_version = client_version
        self.client_os = client_os

    def init(self, disco=None, handlers=None):
        """Registers handlers and adds version feature in disco"""
        self.dispatcher.registerHandler((MyVersionQuery, self))
        if handlers is None:
            handlers = ()
        for handler, host in handlers:
            self.dispatcher.registerHandler((handler, host))

        if disco is not None:
            disco.root_info.addFeatures(Feature(var='jabber:iq:version'))

    def getVersion(self, jid, from_=None):
        """
        Makes get version query to some JID
        
        :param jid: reciever for get version query
        :param addres: sender for get version query
        :returns: deferred object which waits for result stanza 
        with version info (or error stanza) from query's target
        
        """
        if from_ is None:
            from_ = self.dispatcher.myjid
        query = VersionQuery(host=self,
                             parent=Iq(type_='get', to=jid, from_=from_))
        query.iq.result_class = VersionQuery
        self.dispatcher.send(query.iq)
        return query.iq.deferred
