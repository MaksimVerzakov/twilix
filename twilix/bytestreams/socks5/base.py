import time
import hashlib
import random

from twisted.internet import protocol, reactor, defer, error

from twilix.disco import Feature
from twilix.stanzas import Iq
from twilix import errors

from twilix.bytestreams import genSID
from twilix.bytestreams.socks5 import SOCKS5_NS
from twilix.bytestreams.socks5 import stanzas
from twilix.bytestreams.socks5.proxy65 import XEP65Proxy
from twilix.bytestreams.socks5.socks5 import SOCKSv5Client, STATE_READY

# TODO: activate third party proxy

def hashSID(sid, initiator, target):
    import sha
    s = (u"%s%s%s" % (sid, initiator, target)).encode('utf-8')
    return sha.new(s).hexdigest()

class Socks5ClientFactory(protocol.ClientFactory):
    protocol = SOCKSv5Client
    def __init__(self, host, addr, deferred):
        self.host = host
        self.deferred = deferred
        self.addr = addr

    def buildProtocol(self, addr):
        p = protocol.ClientFactory.buildProtocol(self, addr)
        self.protocol = p
        return p

    def clientConnectionLost(self, connector, reason):
        if self.protocol.state == STATE_READY:
            self.host.host.dataReceived(self.addr, None)
        else:
            self.deferred.errback('connection lost')

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

class InitiationQuery(stanzas.StreamHostQuery):

    def _startClient(self, host, rhost, port, addr):
        d = defer.Deferred()
        f = Socks5ClientFactory(host, addr, d)
        reactor.connectTCP(rhost, port, f)
        return d

    @defer.inlineCallbacks
    def setHandler(self):
        if self.sid not in self.host.sessions:
            raise errors.NotAcceptableException
        # TODO: check in parallel
        for streamhost in self.streamhosts:
            try:
                addr = hashSID(self.sid, self.iq.from_, self.iq.to)
                yield self._startClient(self, streamhost.rhost,
                                        streamhost.port, addr)
            except:
                pass
            else:
                used = stanzas.StreamHostUsed(jid=streamhost.jid)
                used_query = stanzas.StreamHostUsedQuery(sid=self.sid,
                                                         streamhost_used=used)
                iq = self.iq.makeResult()
                iq.link(used_query)
                defer.returnValue(iq)
       
        self.host.sessions[self.sid]['meta']['deferred'].\
            errback(errors.ItemNotFoundException)
        raise errors.ItemNotFoundException

class Socks5Stream(protocol.Factory):
    """ Describe a socks5 (XEP-0060) stream service which allow you
        to pass binary data to another entity even if entity is behind
        firewall or NAT. """
    NS = SOCKS5_NS

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.sessions = {}
        self.connections = {}
        self.port = None

    def buildProtocol(self, addr):
        return XEP65Proxy(self)

    def init(self, disco=None, ifaces=None):
        """
        Initialize the service: register all necessary handlers and add a
        feature to service discovery.
        """

        if disco is not None:
            disco.root_info.addFeatures(Feature(var=SOCKS5_NS))
        
        self.dispatcher.registerHandler((InitiationQuery, self))
        self.streamhosts = []
        self.ifaces = []
        # XXX: add possibility to define ports/interfaces
        if ifaces is None:
            ifaces = (('127.0.0.1', random.randint(1024, 65535)),)
        
        for iface in ifaces:
            try:
                reactor.listenTCP(iface[1], self) #, interface=iface[0])
            except error.CannotListenError:
                pass
            else:
                self.ifaces.append(iface)

    def getTransport(self, sid):
        session = self.sessions[sid]
        c = self.connections[session['hash']]['connection']
        if c:
            return c.transport

    def dataReceived(self, addr, buf):
        connection = self.connections.get(addr)
        if not connection:
            return
        
        connection['callback'](buf, self.sessions[connection['sid']]['meta'])
        if buf is None:
            self.unregisterSession(addr=addr)

    def dataSend(self, sid, buf):
        t = self.getTransport(sid)
        if t:
            t.write(buf)
            return True

    def isActive(self, sid):
        session = self.connections[self.sessions[sid]['hash']]
        return session['connection']

    def registerSession(self, sid, initiator, target, callback, meta=None):
        """
        Register bytestream session to wait for incoming connection.
        """
        d = defer.Deferred(canceller=lambda _: self.unregisterSession(sid=sid))
        meta = {
            'meta': meta,
            'hash': hashSID(sid, initiator, target),
        }
        self.sessions[sid] = meta
        self.connections[meta['hash']] = {'sid': sid,
                                          'connection': None,
                                          'callback': callback,
                                          'established_deferred': d}
        return d

    def unregisterConnection(self, sid=None, addr=None):
        if sid is not None:
            addr = self.sessions.get(sid, {}).get('hash')
        if addr is not None and self.connections.has_key(addr):
            sid = self.connections[addr]['sid']
            connection = self.connections[addr]['connection']
            if connection:
                connection.transport.loseConnection()
            del self.connections[addr]
            return sid

    def unregisterSession(self, sid=None, addr=None):
        if sid is None:
            sid = self.unregisterConnection(addr=addr)
        elif self.sessions.has_key(sid):
            self.unregisterConnection(sid=sid)
        if sid is not None:
            del self.sessions[sid]

    @defer.inlineCallbacks
    def requestStream(self, jid, callback, sid=None, meta=None, from_=None):
        """
        Request bytestream session from another entity.

        :param jid: JID of entity we want connect to.

        :param callback: callback which will be called when data will
        be available to consume.

        :param sid: session id to use with stream. Generate one if None given.

        :param meta: metadata for this session. (Will be passed in a callback)

        :param from_: sender JID for request (if differs from myjid)
        """
        if from_ is None:
            from_ = self.dispatcher.myjid
        if sid is None:
            sid = genSID()

        streamhosts = [
            stanzas.StreamHost(rhost=iface[0],
                               jid=from_,
                               port=iface[1]) for iface in self.ifaces
        ]
        query = stanzas.StreamHostQuery(sid=sid,
                                streamhosts=streamhosts,
                                parent=Iq(type_='set', to=jid, from_=from_))

        # XXX: timeout here
        # TODO: connect to other proxies
        # TODO: populate proxies list and streamhosts
        d = self.registerSession(sid, from_, jid, callback, meta=meta)
        try:
            yield self.dispatcher.send(query.iq)
        except:
            self.unregisterSession(sid=sid)
            raise
        yield d
        defer.returnValue(sid)
