import twisted.words.protocols.jabber.client as twisted_client
from twisted.internet import defer, reactor
from twisted.names.srvconnect import SRVConnector
from twisted.words.protocols.jabber.xmlstream import XmlStreamFactory
from twisted.words.protocols.jabber import xmlstream

from twilix.dispatcher import Dispatcher
from twilix.jid import internJID

class InjectFactory(object):
    def clientConnectionLost(self, connector, reason):
        self._fail(connector, reason)

    def clientConnectionFailed(self, connector, reason):
        self._fail(connector, reason)

    def _fail(self, connector, reason):
        XmlStreamFactory.clientConnectionFailed(self, connector, reason)
        if not self._callID:
            self.client.onInitFailed(reason)

class MyXmlStreamFactory(InjectFactory, XmlStreamFactory):
    pass

class XMPPClientConnector(SRVConnector):
    def __init__(self, reactor, domain, factory):
        SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)

class TwilixClient(object):
    def __init__(self, myjid):
        self.myjid = internJID(myjid)

    def generic_connect(self, factory, connector):
        self.f = factory
        self.f.bootstraps = (
            (xmlstream.STREAM_CONNECTED_EVENT, self.onConnected),
            (xmlstream.STREAM_END_EVENT, self.onDisconnected),
            (xmlstream.STREAM_AUTHD_EVENT, self.onAuthenticated),
            (xmlstream.INIT_FAILED_EVENT, self.onInitFailed),
        )
        self.f.client = self
        self.connector = connector
        self.connector.connect()
        self.xmlstream = None

        self.deferred = defer.Deferred()
        return self.deferred

    def connect(self, secret, host=None):
        a = twisted_client.XMPPAuthenticator(self.myjid, secret)
        factory = MyXmlStreamFactory(a)
        factory.maxRetries = 2

        if host is None:
            host = self.myjid.host
        connector = XMPPClientConnector(reactor, host, factory)

        return self.generic_connect(factory, connector)

    def onConnected(self, xs):
        self.xmlstream = xs

    def onAuthenticated(self, xs):
        self.myjid = internJID(unicode(xs.authenticator.jid))
        self.dispatcher = Dispatcher(xs, self.myjid)
        self.init()
        self.deferred.callback(self)
        self.deferred = None

    def onDisconnected(self, failure):
        pass

    def init(self):
        """ Must be redefined in derived classes. Used to initialize all
        needed services and handlers."""

    def onInitFailed(self, failure):
        if self.deferred:
            self.deferred.errback(failure)
            self.deferred = None

