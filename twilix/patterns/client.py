import twisted.words.protocols.jabber.client as twisted_client
from twisted.internet import defer, reactor
from twisted.names.srvconnect import SRVConnector
from twisted.words.protocols.jabber.xmlstream import XmlStreamFactory
from twisted.words.protocols.jabber import xmlstream

from twilix.dispatcher import Dispatcher
from twilix.jid import internJID

class XMPPClientConnector(SRVConnector):
    def __init__(self, reactor, domain, factory, port=5222):
        self.port = port
        SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)

class TwilixClient(object):
    def __init__(self, myjid):
        self.myjid = internJID(myjid)

    def connect(self, secret, host=None, port=None):
        a = twisted_client.XMPPAuthenticator(self.myjid, secret)
        self.f = XmlStreamFactory(a)
        self.f.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.onConnected)
        self.f.addBootstrap(xmlstream.STREAM_END_EVENT, self.onDisconnected)
        self.f.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.onAuthenticated)
        self.f.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.onInitFailed)

        if port is None:
            port = 5222
        if host is None:
            host = self.myjid.host
        self.connector = XMPPClientConnector(reactor, host, self.f, port)
        self.connector.connect()

        self.xmlstream = None

        self.deferred = defer.Deferred()
        return self.deferred

    def onConnected(self, xs):
        self.xmlstream = xs

    def onAuthenticated(self, xs):
        self.dispatcher = Dispatcher(xs, self.myjid)
        self.init()
        self.deferred.callback(self)

    def onDisconnected(self, _):
        pass

    def init(self):
        """ Must be redefined in derived classes. Used to initialize all
        needed services and handlers."""

    def onInitFailed(self, failure):
        self.deferred.errback(failure)

