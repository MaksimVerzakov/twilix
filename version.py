from twilix.stanzas import Query, MyIq
from twilix.disco import Feature
from twilix import fields

class VersionQuery(Query):
    elementUri = 'jabber:iq:version'

    client_name = fields.StringNode('name', required=False)
    client_version = fields.StringNode('version', required=False)
    client_os = fields.StringNode('os', required=False)

class MyVersionQuery(VersionQuery):
    parentClass = MyIq

    def getHandler(self):
        iq = self.iq.makeResult()
        query = VersionQuery(client_name=self.host.client_name,
                             client_version=self.host.client_version,
                             client_os=self.host.client_os,
                             parent=iq)
        return iq

    def setHandler(self):
        return self.iq.makeError('cancel', 'bad-request')

class ClientVersion(object):
    def __init__(self, dispatcher, client_name=None, client_version=None,
                 client_os=None):
        self.dispatcher = dispatcher
        self.client_name = client_name
        self.client_version = client_version
        self.client_os = client_os

    def init(self, disco=None, handlers=None):
        self.dispatcher.registerHandler((MyVersionQuery, self))
        if handlers is None:
            handlers = ()
        for handler, host in handlers:
            self.dispatcher.registerHandler((handler, host))

        if disco is not None:
            disco.root_info.addFeatures(Feature(var='jabber:iq:version'))

    def getVersion(self, jid, cb, from_=None):
        if from_ is None:
            from_ = self.dispatcher.myjid
        query = VersionQuery(host=self,
                             parent=Iq(type_='get', to=jid, from_=from_))
        query.iq.result_class = VersionQuery
        return query.iq.deferred
