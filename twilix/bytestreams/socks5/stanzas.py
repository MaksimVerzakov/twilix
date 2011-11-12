from twilix.stanzas import Query
from twilix.base.velement import VElement
from twilix import fields
from twilix import errors

from twilix.bytestreams.socks5 import SOCKS5_NS

class Socks5Query(Query):
    elementUri = SOCKS5_NS

class Socks5QueryWithSid(Socks5Query):
    sid = fields.StringAttr('sid')

class StreamHost(VElement):
    elementName = 'streamhost'

    rhost = fields.StringAttr('host')
    jid = fields.JidAttr('jid')
    port = fields.StringAttr('port')

    def clean_port(self, value):
        try:
            value = int(value)
            assert value < 65536
        except (ValueError, TypeError, AssertionError):
            raise NotAcceptableException
        return value

class StreamHostQuery(Socks5QueryWithSid):
    streamhosts = fields.ElementNode(StreamHost, listed=True)

class StreamHostUsed(VElement):
    elementName = 'streamhost-used'

    jid = fields.JidAttr('jid')

class StreamHostUsedQuery(Socks5QueryWithSid):
    streamhost_used = fields.ElementNode(StreamHostUsed)

