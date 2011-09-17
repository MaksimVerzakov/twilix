"""Module provides In-Band Registration mechanism."""

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
    """Class describes interaction dispatcher with register."""
    def __init__(self, dispatcher):
        """Set dispatcher."""
        self.dispatcher = dispatcher

    def init(self, handler, disco=None):
        """Registers handlers and adds version feature in disco."""
        handler, host = handler
        self.dispatcher.registerHandler((handler, host))
        if disco is not None:
            disco.root_info.addFeatures((Feature(var='jabber:iq:register')))

