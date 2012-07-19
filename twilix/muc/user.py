from pydispatch import dispatcher

from twilix.stanzas import Presence
from twilix.base.velement import VElement
from twilix import fields

class UserItemInfo(VElement):
    """
    VElement-inheritor class for user info from xml stanzas.
    Used in multi-user chat presences and also in administrator's queries.

    """
    elementName = 'item'
    elementUri = 'http://jabber.org/protocol/muc#user'

    affiliation = fields.StringAttr('affiliation', required=False)
    role = fields.StringAttr('role', required=False)
    nick = fields.StringAttr('nick', required=False)
    jid = fields.JidAttr('jid', required=False)
    
    reason = fields.StringNode('reason', required=False)

class UserItem(VElement):
    """
    VElement-inheritor class container for user info class.
    
    Attributes : 
        
        item -- UserItemInfo-type user's info class
        
    """
    elementName = 'x'
    elementUri = 'http://jabber.org/protocol/muc#user'
    
    item = fields.ElementNode(UserItemInfo, required=False)

class UserPresence(Presence):
    """
    Presence-inheritor class for multi user chat occupant's info.
    Also handles user online/offline presences.
    
    Attributes :
        
        user -- UserItem-type node for information about user.
        
    Methods : 
        
        anyHandler -- handles all of this type presences.
        
    """   
        
    user = fields.ElementNode(UserItem, required=False)
    
    def anyHandler(self):
        """
        Changes list of info about users in chat.
        There is addition in roster for 'available'-type presences and 
        deletion from roster for 'unavailable'-type.
        Also sends 'user_available'/'user_unavailbale' signals for dispatcher 
        (from pydispatch module).
        
        """
                
        if self.user is None:
            return
        
        room_jid = self.from_.bare()
        if room_jid not in self.host.roster:
            return
        
        self.host.roster[room_jid] = filter(lambda el: el.from_.resource != self.from_.resource, self.host.roster[room_jid])
        
        if self.type_ == 'unavailable':
            dispatcher.send(self.host.user_unavailable, user=self)
        else:
            self.host.roster[room_jid].append(self)
            dispatcher.send(self.host.user_available, user=self)
