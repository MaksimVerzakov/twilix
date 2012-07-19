from twilix.stanzas import Presence
from twilix.base.velement import VElement

class ConnectPresence(VElement):
    """
    VElement-inheritor class for connection to multi-user chat.
    """
    parentClass = Presence
    elementName ='x'
    elementUri = 'http://jabber.org/protocol/muc'
    
