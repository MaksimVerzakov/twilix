import sha
import time
import hashlib
import random
import warnings

from twisted.internet import protocol, reactor, defer, error

from twilix.disco import Feature
from twilix.stanzas import Iq
from twilix import errors

from twilix.bytestreams import genSID
from twilix.bytestreams.socks5 import SOCKS5_NS
from twilix.bytestreams.socks5 import stanzas
from twilix.bytestreams.socks5.proxy65 import XEP65Proxy
from twilix.bytestreams.socks5.socks5 import SOCKSv5Client, STATE_READY

def hashSID(sid, initiator, target):
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
            self.host.dataReceived(self.addr, None)
        else:
            self.deferred.errback('connection lost')

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

def _startClient(host, rhost, port, addr):
    d = defer.Deferred()
    f = Socks5ClientFactory(host, addr, d)
    reactor.connectTCP(rhost, port, f)
    return d

class InitiationQuery(stanzas.StreamHostQuery):

    def setHandler(self):
        if self.sid not in self.host.sessions:
            raise errors.NotAcceptableException
        deferreds = []
        time_calls = []

        def _eb(failure, d):
            """ Errorback for a streamhost candidate """
            # Remove this deferred from wait list
            if d is not None:
                deferreds.remove(d)
            # If there is no more candidates to check and we still did not
            # callback then we raise ItemNotFound because we can't connect
            # to any candidate
            if not deferreds and not time_calls and not my_defer.called:
                self.host.sessions[self.sid]['meta']['deferred'].\
                    errback(errors.ItemNotFoundException())
                my_defer.errback(errors.ItemNotFoundException())
                
        def _cb(result, d, streamhost):
            """ Callback for a streamhost candidate """
            # Okay, we've found the candidate, let's generate a reply
            used = stanzas.StreamHostUsed(jid=streamhost.jid)
            used_query = stanzas.StreamHostUsedQuery(sid=self.sid,
                                                     streamhost_used=used)
            iq = self.iq.makeResult()
            iq.link(used_query)
            my_defer.callback(iq)

            # Clean up all ongoing checks
            for time_call in time_calls:
                time_call.cancel()
            for defer in deferreds:
                defer.cancel()
        
        def i():
            # An iterator which iterates through deferreds to check
            for streamhost in self.streamhosts:
                addr = hashSID(self.sid, self.iq.from_, self.iq.to)
                d = _startClient(self.host, streamhost.rhost,
                                 streamhost.port, addr)
                d.addCallback(_cb, d, streamhost)
                d.addErrback(_eb, d)
                deferreds.append(d)
                yield

        def later(iterator, interval=3):
            """ Call iterators with a given interval """
            # Remove earliest time call if it exists
            if time_calls:
                time_calls.pop(0)
            # Iterate to a next streamhost
            try:
                iterator.next()
            except StopIteration:
                # We don't have to test anything now, call errorback to clean
                _eb(None, None)
            else:
                # Call next deferred after the interval
                _later(iterator, interval)
        def _later(iterator, interval):
            time_calls.append(reactor.callLater(5, later, iterator))
        
        iterator = i()
        later(iterator)

        my_defer = defer.Deferred()
        return my_defer

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
        self.proxies = {}

    def buildProtocol(self, addr):
        return XEP65Proxy(self)

    def init(self, disco=None, ifaces=None, port=None):
        """
        Initialize the service: register all necessary handlers and add a
        feature to service discovery.
        """

        if disco is not None:
            disco.root_info.addFeatures(Feature(var=SOCKS5_NS))
        
        self.dispatcher.registerHandler((InitiationQuery, self))
        self.disco = disco
        self.streamhosts = []
        self.ifaces = []
        if ifaces is None:
            ifaces = self.__get_my_addresses(port)
        
        for iface in ifaces:
            try:
                reactor.listenTCP(iface[1], self) #, interface=iface[0])
            except error.CannotListenError:
                pass
            else:
                self.ifaces.append(iface)
        if self.dispatcher.myjid.user and disco:
            self.populate_proxies(self.dispatcher.myjid.host)

    def __get_my_addresses(self, port):
        try:
            from netifaces import ifaddresses, AF_INET, interfaces
        except ImportError:
            warnings.warn(
            "Install the netifaces library to be able to gather info about\
    your IP address to make proxy65 work better", RuntimeWarning)
            return []

        for ifname in interfaces():
            addresses = \
            [i['addr'] for i in ifaddresses(ifname).setdefault(AF_INET,
                                                        [{'addr': None}]) if \
                                                                i.get('addr')]
        ifaces = []
        if port is None:
            port = random.randint(1024, 65535)
        for addr in addresses:
            ifaces.append((addr, port))
        return ifaces

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
    def populate_proxies(self, server_jid, from_=None):
        assert self.disco
        if from_ is None:
            from_ = self.dispatcher.myjid
        result = yield self.disco.getItems(server_jid, from_=from_)
        proxies = []
        for item in result.items:
            try:
                info = yield self.disco.getInfo(item.jid, from_=from_)
            except errors.ExceptionWithType:
                continue
            if filter(lambda i: i.var == SOCKS5_NS, info.features):
                proxies.append(item.jid)
        for jid in proxies:
            try:
                yield self.examine_proxy(jid, from_)
            except errors.ExceptionWithType:
                pass

    @defer.inlineCallbacks
    def examine_proxy(self, jid, from_):
        query = stanzas.GetStreamHostsQuery(
                 parent=Iq(from_=from_, to=jid, type_='get'))
        result = yield self.dispatcher.send(query)
        r = result.streamhost
        result = (r.rhost, r.port)
        self.proxies[query.iq.to] = result

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

        for proxy_jid in self.proxies:
            proxy = self.proxies[proxy_jid]
            streamhosts.append(
                stanzas.StreamHost(rhost=proxy[0],
                                   port=proxy[1],
                                   jid=proxy_jid)
            )

        query = stanzas.StreamHostQuery(sid=sid,
                                streamhosts=streamhosts,
                                parent=Iq(type_='set', to=jid, from_=from_))

        d = self.registerSession(sid, from_, jid, callback, meta=meta)
        try:
            result = yield self.dispatcher.send(query)
        except:
            self.unregisterSession(sid=sid)
            raise
        pjid = result.streamhost_used.jid
        if pjid in self.proxies:
            proxy = self.proxies[pjid]
            yield _startClient(self, proxy[0], proxy[1], 
                               self.sessions[sid]['hash'])
            query = stanzas.ActivateQuery(jid=jid, sid=sid,
                        parent=Iq(type_='set', from_=from_,
                                  to=pjid))
            yield self.dispatcher.send(query)
        else:
            yield d
        defer.returnValue(sid)
