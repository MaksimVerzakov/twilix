import base64
import hashlib
import time

from twisted.internet import defer, reactor

from twilix.bytestreams import genSID
from twilix.bytestreams.ibb import IBB_NS
from twilix.bytestreams.ibb.stanzas import OpenQuery, CloseQuery as CQ,\
                                            DataQuery as DQ
from twilix.jid import internJID
from twilix.stanzas import Iq
from twilix import errors

class PersonsValidator(object):
    def validate_persons(self):
        s = self.host.sessions[self.sid]
        persons = (s['initiator'], s['target'])
        if self.iq.from_ not in persons or self.iq.to not in persons:
            raise errors.ItemNotFoundException

class InitiationQuery(OpenQuery, PersonsValidator):
    def setHandler(self):
        if self.sid not in self.host.sessions:
            raise errors.NotAcceptableException
        self.validate_persons()
        self.host.sessions[self.sid]['block_size'] = self.block_size
        self.host.sessions[self.sid]['active'] = True
        return self.iq.makeResult()

class CloseQuery(CQ, PersonsValidator):
    def setHandler(self):
        if self.sid not in self.host.sessions or \
            not self.host.sessions[self.sid]['active']:
            raise errors.ItemNotFoundException
        self.validate_persons()
        self.host.dataReceived(self.sid, None)
        return self.iq.makeResult()

class DataQuery(DQ, PersonsValidator):
    def setHandler(self):
        # XXX: message stanzas support
        # XXX: StringIO support?
        if self.sid not in self.host.sessions or \
            not self.host.sessions[self.sid]['active']:
            raise errors.ItemNotFoundException
        self.validate_persons()
        s = self.host.sessions[self.sid]
        c = self.content.strip()
        if len(c) > s['block_size']:
            raise errors.NotAcceptableException
        if self.seq != s['incoming_seq']:
            raise errors.UnexpectedRequestException
        s['incoming_seq'] += 1
        s['incoming_seq'] = s['incoming_seq'] % 65536
        try:
            buf = base64.b64decode(c)
        except TypeError:
            raise errors.BadRequestException
        self.host.dataReceived(self.sid, buf)
        return self.iq.makeResult()

class IbbStream(object):
    """ Describe a in-band bytestream service which allow you
        to pass binary data through an XML-stream. """

    def __init__(self, dispatcher, send_interval=1):
        self.dispatcher = dispatcher
        self.sessions = {}
        self.send_interval = send_interval
        
    def init(self, disco=None):
        if disco is not None:
            self.disco.root_info.addFeatures(Feature(var=IBB_NS))

        self.dispatcher.registerHandler((InitiationQuery, self))
        self.dispatcher.registerHandler((DataQuery, self))
        self.dispatcher.registerHandler((CloseQuery, self))

    def dataReceived(self, sid, buf):
        session = self.sessions[sid]
        session['callback'](buf, session['meta'])
        if buf is None:
            self.unregisterSession(sid=sid)

    def dataSend(self, sid, buf):
        if self.sessions[sid]['active']:
            self.sessions[sid]['buf'] += buf
            return True

    def isActive(self, sid):
        return self.sessions[sid]['active']

    @defer.inlineCallbacks
    def _dataSend(self, sid):
        # XXX: Error handling
        s = self.sessions[sid]
        if not s['active']:
            return
        if not s['buf']:
            if s['closing']:
                self._unregisterConnection(sid)
            return
        toSend = ''
        i = 0
        l = 0
        while True:
            chunk = s['buf'][i * 100:i * 100 + 100]
            e = base64.b64encode(chunk)
            new_l = len(e)
            if l + new_l > s['block_size'] or not chunk:
                break
            i += 1
            toSend += chunk
            l += new_l
        toSend = base64.b64encode(toSend)
        s['buf'] = s['buf'][i * 100:]
        dq = DQ(seq=s['outgoing_seq'],
                sid=sid,
                parent=Iq(to=s['initiator'],
                          from_=s['target'],
                          type_='set'))
        s['outgoing_seq'] += 1
        if s['is_outgoing']:
            dq.iq.swapAttributeValues('to', 'from')
        dq.content = toSend
        if s['wait_for_result_when_send']:
            yield self.dispatcher.send(dq.iq)
        else:
            self.dispatcher.send(dq.iq)
        
        if s['buf']:
            reactor.callWhenRunning(self._dataSend, sid)
        else:
            reactor.callLater(self.send_interval, self._dataSend, sid)

    def registerSession(self, sid, initiator, target, callback, meta=None,
                        block_size=None, stanza_type='iq',
                        wait_for_result_when_send=True):
        """
        Register bytestream session to wait for incoming connection.
        """
        if isinstance(initiator, (str, unicode)):
            initiator = internJID(initiator)
        if isinstance(target, (str, unicode)):
            target = internJID(target)
        meta = {
            'initiator': initiator,
            'target': target,
            'callback': callback,
            'meta': meta,
            'active': False,
            'block_size': block_size,
            'stanza_type': stanza_type,
            'incoming_seq': 0,
            'outgoing_seq': 0,
            'wait_for_result_when_send': wait_for_result_when_send,
            'buf': '',
            'is_outgoing': False,
            'closing': False,
        }
        self.sessions[sid] = meta
        reactor.callLater(self.send_interval, self._dataSend, sid)
        return meta

    def unregisterConnection(self, sid):
        s = self.sessions[sid]
        if not s['active']:
            return
        s['closing'] = True

    def _unregisterConnection(self, sid):
        s = self.sessions[sid]
        if not s['closing']:
            return
        cq = CQ(sid=sid,
                parent=Iq(to=s['initiator'],
                          from_=s['target'],
                          type_='set'))
        if s['is_outgoing']:
            cq.iq.swapAttributeValues('to', 'from')
        return self.dispatcher.send(cq.iq)

    def unregisterSession(self, sid):
        if self.sessions.has_key(sid):
            s = self.sessions[sid]
            self.unregisterConnection(sid)
            del self.sessions[sid]
            return True

    @defer.inlineCallbacks
    def requestStream(self, jid, callback, sid=None, meta=None, from_=None,
                      block_size=4096, stanza_type='iq',
                      wait_for_result_when_send=True):
        """
        Request bytestream session from another entity.

        :param jid: JID of entity we want connect to.

        :param callback: callback which will be called when data will
        be available to consume.

        :param sid: session id to use with stream. Generate one if None given.

        :param meta: metadata for this session. (Will be passed in a callback)

        :param from_: sender JID for request (if differs from myjid)

        :param block_size: block size to use with the connection.
        """
        # XXX: generate sid
        if from_ is None:
            from_ = self.dispatcher.myjid

        if sid is None:
            sid = genSID()
        s = self.registerSession(sid, from_, jid, callback, meta=meta,
                             block_size=block_size, stanza_type=stanza_type,
                         wait_for_result_when_send=wait_for_result_when_send)
        s['is_outgoing'] = True
        query = OpenQuery(block_size=block_size,
                          sid=sid,
                          stanza_type=stanza_type,
                          parent=Iq(type_='set', to=jid, from_=from_))
        try:
            yield self.dispatcher.send(query.iq)
        except:
            self.unregisterSession(sid=sid)
            raise
        
        s['active'] = True
        defer.returnValue(sid)
