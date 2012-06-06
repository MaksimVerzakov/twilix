from twilix.base import VElement
from twilix.stanzas import Message

class Delay(VElement):
    """
    VElement-inheritor class for offline messages.
    """
    elementName = 'delay'
    elementUri = 'urn:xmpp:delay'
    
    parentClass = Message
