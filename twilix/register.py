"""Module provides In-Band Registration mechanism. (XEP-0077)

Can be used to provide registration ability to your XMPP-enabled service."""

from twilix.stanzas import Query, MyIq
from twilix.disco import Feature
from twilix import fields

class RegisterQuery(Query):
    """
    Extends Query class. 
    Contains special fields described in XEP-0077 for register query.
    
    Attributes:
        instructions -- string node 'instructions'
        
        registered -- flag node 'registered'
        
        remove -- flag node 'remove'
        
    """
    elementUri = 'jabber:iq:register'

    instructions = fields.StringNode('instructions', required=False)
    registered = fields.FlagNode('registered', required=False)
    aremove = fields.FlagNode('remove', required=False)
    # TODO: support of jabber:x:data

class MyRegisterQuery(RegisterQuery):
    """
    Extends RegisterQuery class.
    Set MyIQ as parent class to have an ability to override 
    validating class.
    """
    parentClass = MyIq

class Register(object):
    """Class describes interaction dispatcher with register.
    
    :param dispatcher: dispatcher to use with the service."""
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def init(self, handler, disco=None):
        """Registers handlers and adds the register feature in disco."""
        handler, host = handler
        self.dispatcher.registerHandler((handler, host))
        if disco is not None:
            disco.root_info.addFeatures((Feature(var='jabber:iq:register')))

