from twilix.stanzas import Message

class Delay(Message):
    """
    Class for chat history in multi chat room.
    """
    elementName = 'delay'
    elementUri = 'urn:xmpp:delay'
