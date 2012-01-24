from twilix.stanzas import Query, Message
from twilix import errors
from twilix import fields
from twilix.base.velement import VElement

from twilix.bytestreams.ibb import IBB_NS

class IbbQuery(Query):
    elementUri = IBB_NS

class OpenQuery(IbbQuery):
    elementName = 'open'

    block_size = fields.StringAttr('block-size')
    sid = fields.StringAttr('sid')
    stanza_type = fields.StringAttr('stanza', required=False)

    def clean_block_size(self, value):
        try:
            value = int(value)
            assert value <= 65535
        except (ValueError, TypeError, AssertionError):
            raise errors.BadRequestException
        return value

    def clean_stanza(self, value):
        if value not in ('iq', 'message'):
            raise errors.BadRequestException
        return value

class DataElement(VElement):
    elementName = 'data'
    elementUri = IBB_NS

    seq = fields.StringAttr('seq')
    sid = fields.StringAttr('sid')

    def clean_seq(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError, AssertionError):
            raise errors.BadRequestException
        value = value % 65536
        return value

class DataQuery(DataElement, Query):
    pass

class MessageDataQuery(DataElement):
    parentClass = Message

class CloseQuery(IbbQuery):
    elementName = 'close'

    sid = fields.StringAttr('sid')

