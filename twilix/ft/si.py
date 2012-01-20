from twisted.internet import defer
from twisted.protocols.basic import FileSender

from twilix.si import SIProfile, SIRequest, Feature
from twilix.base.velement import VElement
from twilix import errors
from twilix import fields

PROFILE_NS = 'http://jabber.org/protocol/si/profile/file-transfer'

class File(VElement):
    elementName = 'file'
    elementUri = PROFILE_NS

class Range(VElement):
    elementName = 'range'

    length = fields.IntegerAttr('length', required=False)
    offset = fields.IntegerAttr('offset', required=False)

class FileRequest(File):
    name_ = fields.StringAttr('name')
    size = fields.IntegerAttr('size')
    hash_ = fields.StringAttr('hash', required=False)
    date = fields.DateTimeAttr('date', required=False)
    description = fields.StringNode('desc', required=False)
    range_ = fields.ElementNode(Range, required=False)

class FTSIRequest(SIRequest):
    file_ = fields.ElementNode(FileRequest)

    @defer.inlineCallbacks
    def setHandler(self):
        reply, deferred, meta = self.make_reply(self.host.si)
        buf = yield self.host.cb(self, deferred)
        if buf is None:
            # TODO: application specific error
            raise errors.ForbiddenException
        meta.update({
            'buf': buf,
            'size': self.file_.size,
            'bytes_read': 0,
            'deferred': deferred,
        })
        defer.returnValue(reply)

class SIFileTransferProfile(SIProfile):
    handlerClass = FTSIRequest
    NS = PROFILE_NS

    def __init__(self, si, cb, *args, **kwargs):
        super(SIFileTransferProfile, self).__init__(si, *args, **kwargs)
        self.cb = cb

    @defer.inlineCallbacks
    def send_file(self, to, buf, filename, size=None,
                  description=None, date=None, from_=None):
        if size is None:
            buf.seek(0, 2)
            size = buf.tell()
            buf.seek(0)
        fr = FileRequest(name_=filename,
                         size=size,
                         date=date,
                         description=description)
        req = FTSIRequest(file_=fr, profile=PROFILE_NS)
        stream, sid = yield self.si.initiate(req, to, from_)
        yield FileSender().beginFileTransfer(buf, stream.getTransport(sid))
        stream.unregisterSession(sid=sid)

