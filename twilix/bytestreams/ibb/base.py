import base64
import hashlib
import time

from twisted.internet import defer, reactor

from twilix.bytestreams import genSID
from twilix.bytestreams.ibb import IBB_NS
from twilix.bytestreams.ibb.stanzas import OpenQuery, CloseQuery as CQ,\
                                            DataQuery as DQ,\
                                            MessageDataQuery as MDQ
from twilix.jid import internJID
from twilix.stanzas import Iq
from twilix import errors
from twilix.disco import Feature

class PersonsValidator(object):
    def validate_persons(self):
        s = self.host.sessions[self.sid]
        persons = (s['initiator'], s['target'])
        top = self.topElement()
        if top.from_ not in persons or top.to not in persons:
            raise errors.ItemNotFoundException

class InitiationQuery(OpenQuery, PersonsValidator):
    def setHandler(self):
        if self.sid not in self.host.sessions:
            raise errors.NotAcceptableException
        self.validate_persons()
        self.host.sessions[self.sid]['block_size'] = self.block_size
        self.host.sessions[self.sid]['active'] = True
        if self.stanza == 'message':
            self.host.session[self.sid]['stanza'] = 'message'
        return self.iq.makeResult()

class CloseQuery(CQ, PersonsValidator):
    def setHandler(self):
        if self.sid not in self.host.sessions or \
            not self.host.sessions[self.sid]['active']:
            raise errors.ItemNotFoundException
        self.validate_persons()
        self.host.unregisterSession(sid=self.sid)
        return self.iq.makeResult()

class DataHandler(object):
    def handler(self):
        if self.sid not in self.host.sessions or \
            not self.host.sessions[self.sid]['active']:
            raise errors.ItemNotFoundException
        self.validate_persons()
        s = self.host.sessions[self.sid]
        c = self.content.strip()
        if len(c) > s['block_size'] * 2: 
            raise errors.NotAcceptableException
        if self.seq != s['incoming_seq']:
            raise errors.UnexpectedRequestException
        s['incoming_seq'] += 1
        s['incoming_seq'] = s['incoming_seq'] % 65536
        try:
            buf = base64.b64decode(c)
        except TypeError:
            raise errors.BadRequestException
        if len(buf) > s['block_size']:
            raise errors.NotAcceptableException
        self.host.dataReceived(self.sid, buf)
        iq = self.iq
        if iq:
            return iq.makeResult()
        # XXX: return EmptyStanza here?
    
class DataQuery(DataHandler, DQ, PersonsValidator):
    def setHandler(self):
        return self.handler()

class DataMessage(DataHandler, MDQ, PersonsValidator):
    def anyHandler(self):
        if self.topElement().type_ != 'error':
            return self.handler()

class Transport(object):
    def __init__(self, sid, session, dispatcher, interval):
        self.session = session
        self.dispatcher = dispatcher
        self.sid = sid
        self.producer = None
        self.interval = interval
        self.buf = ''
        self._produce()
        
    def write(self, buf):
        self.buf += buf

    @defer.inlineCallbacks
    def _write(self):
        # XXX: Error handling
        if not self.session['active']:
            defer.returnValue(None)
        toSend = self.buf[:self.session['block_size']]
        self.buf = self.buf[self.session['block_size']:]
        toSend = base64.b64encode(toSend)
        dq = DQ(seq=self.session['outgoing_seq'],
                sid=self.sid,
                parent=Iq(to=self.session['initiator'],
                          from_=self.session['target'],
                          type_='set'))
        self.session['outgoing_seq'] += 1
        if self.session['is_outgoing']:
            dq.iq.swapAttributeValues('to', 'from')
        dq.content = toSend
        if self.session['wait_for_result_when_send']:
            yield self.dispatcher.send(dq.iq)
        else:
            self.dispatcher.send(dq.iq)

    def registerProducer(self, producer, streaming):
        assert streaming == False
        self.producer = producer
        self._produce()
    
    def _produce(self):
        if self.buf:
            self._write()
        elif self.producer:
            self.producer.resumeProducing()
        reactor.callLater(self.interval, self._produce)

    def unregisterProducer(self):
        self.producer = None

class IbbStream(object):
    """ Describe a in-band bytestream service which allow you
        to pass binary data through an XML-stream. """
    NS = IBB_NS

    def __init__(self, dispatcher, send_interval=1):
        self.dispatcher = dispatcher
        self.sessions = {}
        self.send_interval = send_interval
        
    def init(self, disco=None):
        if disco is not None:
            disco.root_info.addFeatures(Feature(var=IBB_NS))

        self.dispatcher.registerHandler((InitiationQuery, self))
        self.dispatcher.registerHandler((DataQuery, self))
        self.dispatcher.registerHandler((DataMessage, self))
        self.dispatcher.registerHandler((CloseQuery, self))

    def dataReceived(self, sid, buf, dont_unregister=False):
        session = self.sessions[sid]
        session['callback'](buf, session['meta'])
        if buf is None and not dont_unregister:
            self.unregisterSession(sid=sid)

    def dataSend(self, sid, buf):
        t = self.getTransport(sid)
        if t:
            t.write(buf)
            return True

    def getTransport(self, sid):
        if self.sessions[sid]['active']:
            return self.sessions[sid]['transport']

    def isActive(self, sid):
        return self.sessions[sid]['active']

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
            'is_outgoing': False,
            'stanza': 'iq',
        }
        meta['transport'] = Transport(sid, meta, self.dispatcher,
                                      self.send_interval)
        self.sessions[sid] = meta
        return meta

    def unregisterConnection(self, sid):
        s = self.sessions[sid]
        if not s['active']:
            return
        self.dataReceived(sid, None, dont_unregister=True)
        self._unregisterConnection(sid)

    def _unregisterConnection(self, sid):
        s = self.sessions[sid]
        cq = CQ(sid=sid,
                parent=Iq(to=s['initiator'],
                          from_=s['target'],
                          type_='set'))
        if s['is_outgoing']:
            cq.iq.swapAttributeValues('to', 'from')
        self.getTransport(sid).unregisterProducer()
        s['active'] = False
        del self.sessions[sid]
        return self.dispatcher.send(cq.iq)

    def unregisterSession(self, sid):
        if self.sessions.has_key(sid):
            s = self.sessions[sid]
            self.unregisterConnection(sid)
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
