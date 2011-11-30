"""
Module implements vcard-temp feature. (XEP-0054)

Can be used to serve own vcard (for services), set own vcard (for clients) and
view vcards of other entities.
"""
import copy

from twilix.stanzas import Query, Iq
from twilix import fields
from twilix.disco import Feature
from twilix.base.velement import VElement
from twilix import errors

class Name(VElement):
    """
    Extends VElement class from twilix.base.
    Used for representation name data.
    
    Attributes:
        family_name -- string node 'FAMILY'
        
        given_name -- string node 'GIVEN'
        
        middle_name -- string node 'MIDDLE'
        
    """    
    elementName = 'N'
    
    family_name = fields.StringNode('FAMILY', required=False)
    given_name = fields.StringNode('GIVEN', required=False)
    middle_name = fields.StringNode('MIDDLE', required=False)

class Organization(VElement):
    """
    Extends VElement class from twilix.base.
    Used for representation organization data.
    
    Attributes:
        name -- string node 'ORGNAME'
        
        unit -- string node 'ORGUNIT'
        
    """
    elementName = 'ORG'

    name_ = fields.StringNode('ORGNAME', required=False)
    unit = fields.StringNode('ORGUNIT', required=False)

class Telephone(VElement):
    # TODO
    """
    Extends VElement class from twilix.base.
    Used for representation telephone data.
    """
    pass

class Address(VElement):
    # TODO
    """
    Extends VElement class from twilix.base.
    Used for representation adress data.
    """
    pass

class Email(VElement):
    # TODO
    """
    Extends VElement class from twilix.base.
    Used for representation e-mail data.
    """
    pass

class Photo(VElement):
    """
    Extends VElement class from twilix.base.
    Used for representation photo data.
    
    Attributes:
        type\_ -- string node 'TYPE'
        
        binval -- base64 node 'BINVAL'
        
    """
    elementName = 'PHOTO'

    type_ = fields.StringNode('TYPE', required=False)
    binval = fields.Base64Node('BINVAL', required=False)

class VCardQuery(Query):
    """
    Extends Query class from twilix.stanzas.
    Contains fields with nodes for personal info.
    """
    elementName = 'vCard'
    elementUri = 'vcard-temp'

    full_name = fields.StringNode('FN', required=False)
    name_ = fields.ElementNode('N', Name, required=False, listed=False)
    nickname = fields.StringNode('NICKNAME', required=False)
    url = fields.StringNode('URL', required=False)
    birthday = fields.StringNode('BDAY', required=False)
    organization = fields.ElementNode('ORG', Organization, required=False,
                                      listed=False)
    title = fields.StringNode('TITLE', required=False)
    role = fields.StringNode('ROLE', required=False)
    # telephones TODO
    # addresses TODO
    # emails TODO
    jid = fields.StringNode('JABBERID', required=False)
    description = fields.StringNode('DESC', required=False)
    photo = fields.ElementNode('PHOTO', Photo, required=False, listed=False)

class MyVCardQuery(VCardQuery):
    """
    Extends VCardQuery.
    Define get and set Handlers.
    """
    def getHandler(self):
        """
        Make result iq with myvcard when dispatcher receives 'get' query.
        
        :returns:
            result iq with myvcard if it's exist and destination is correct.
        
        :raises:
            ItemNotFoundException
            
        """
        if self.host.myvcard and self.host.dispatcher.myjid == self.iq.to:
            iq = self.iq.makeResult()
            iq.link(self.host.myvcard)
            return iq
        elif not self.host.myvcard:
            raise errors.ItemNotFoundException()

    def setHandler(self):
        """Forbid the ability to set vcard."""
        raise errors.ForbiddenException()


class VCard(object):
    """
    Class describes interaction dispatcher with personal info
    in myvcard.

    :param dispatcher: set dispatcher that service should use.

    :param myvcard: set vcard which should be served as own (for services).
    """
    def __init__(self, dispatcher, myvcard=None):
        """Initialize dispatcher, myvcard and list of handlers."""
        self.dispatcher = dispatcher
        self.myvcard = myvcard
        self._handlers = []

    def init(self, disco=None, handlers=None):
        """
        Register necessary handlers and add vcard-temp feature into own disco
        info.

        :param disco: Disco instance to add the feature to.
        
        :param handlers: extra handlers to generate dynamic vcards.

        """
        if handlers is None:
            handlers = ()

        self.dispatcher.registerHandler((MyVCardQuery, self))

        for handler, host in handlers:
            self.dispatcher.registerHandler((handler, host))

        if disco is not None:
            disco.root_info.addFeatures(Feature(var='vcard-temp'))

    def get(self, jid, from_=None):
        """
        Get a vcard of another XMPP entity.
        
        :returns:
            query.iq.deferred with a VCardQuery instance as a result
        """
        if from_ is None:
            from_ = self.dispatcher.myjid
        query = VCardQuery(parent=Iq(type_='get', to=jid, from_=from_))
        query.iq.result_class = VCardQuery
        self.dispatcher.send(query.iq)
        return query.iq.deferred

    def set(self, vcard):
        """
        Set my own vcard (for clients).
        
        :returns:
            query.iq.deferred
        """
        query = copy.copy(vcard)
        iq = Iq(type_='set')
        iq.link(query)
        self.dispatcher.send(query.iq)
        return query.iq.deferred

