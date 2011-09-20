from twisted.internet import defer

from twilix import fields
from twilix.stanzas import Query, Iq

from .user import UserItemInfo

class AdminQuery(Query):
    """
    Query-inheritor class for administrator's queries.
    These queries used for change role or affiliation of chat users.
    
    Attributes :
        
        item -- not required UserItemInfo-type element node.
    
    Methods : 
        
        makeAdminQuery -- method sends query stanza and returns result stanza.
    
    """
    
    elementUri = 'http://jabber.org/protocol/muc#admin'
    item = fields.ElementNode(UserItemInfo, required=False)

@defer.inlineCallbacks
def makeAdminQuery(item, iq, dispatcher):
    """
    Creates query stanza and than sends it to dispatcher.
    
    :param item: UserItemInfo-type element. Contains new values of 
    role/affiliation
    
    :param iq: ItemQuery-type parent for created stanza
    
    :param dispatcher: dispatcher that deals with query stanza and than 
    returns a result stanza
    
    :returns: result stanza for sended query (result- or error- type stanza)
    
    """
    query = AdminQuery(item=item, parent=iq)
    query.iq.result_class = Iq
    dispatcher.send(query.iq)
    defr = query.iq.deferred
    res = yield defr
    defer.returnValue(res)
