from twilix.stanzas import Query, MyIq
from twilix.disco import Feature
from twilix import fields

class RegisterQuery(Query):
    elementUri = 'jabber:iq:register'

    instructions = fields.StringNode('instructions', required=False)
    registered = fields.FlagNode('registered', required=False)
    aremove = fields.FlagNode('remove', required=False)
    # TODO: support of jabber:x:data

class MyRegisterQuery(RegisterQuery):
    parentClass = MyIq

class Register(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def init(self, handler, disco=None):
        handler, host = handler
        self.dispatcher.registerHandler((handler, host))
        if disco is not None:
            disco.root_info.addFeatures((Feature(var='jabber:iq:register')))

