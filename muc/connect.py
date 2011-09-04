from twilix.stanzas import Presence
from twilix.base import VElement

class ConnectPresence(VElement):
    """
    Class for connection to multi chat room.
    """
    parentClass = Presence
    elementName ='x'
    elementUri = 'http://jabber.org/protocol/muc'
    
