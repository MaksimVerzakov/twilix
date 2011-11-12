from twisted.internet import reactor
from twisted.words.protocols.jabber import component

from twilix.dispatcher import Dispatcher
from twilix.jid import internJID

class TwilixComponent(component.Service):
    """ Class to build XMPP components based on twilix. (see XEP-0114)

    Look at the connect method to connect your component to an XMPP-server.
        
    :param myjid: The jid of the component."""
    def __init__(self, myjid):
        self.myjid = internJID(myjid)

    def connect(self, port, secret, host=None):
        """ Connect component to an XMPP-server to make it works.

        :param port: port to connect to. Needs to be set the same as in XMPP
        server config.

        :param secret: a secret to connect to XMPP server.

        :param host: a host to connect to XMPP server. It's needed only
        if host to connect is differ from jid."""

        if host is None:
            host = unicode(self.myjid)
        f = component.componentFactory(unicode(self.myjid), secret)
        connector = component.buildServiceManager(unicode(self.myjid), secret,
                                         "tcp:%s:%s" % (host, port))
        self.setServiceParent(connector)
        connector.startService()

    def componentConnected(self, xs):
        self.xmlstream = xs
        self.dispatcher = Dispatcher(xs, self.myjid)
        self.init()

        self.xmlstream.rawDataInFn = self.rawIn
        self.xmlstream.rawDataOutFn = self.rawOut

    def init(self):
        """ To be overriden in derived classes. Used to initialize all needed
        services """

    def rawIn(self, data):
        print "<<< %s" % data

    def rawOut(self, data):
        print ">>> %s" % data
