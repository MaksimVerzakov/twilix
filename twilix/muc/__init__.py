from twilix.stanzas import Presence, Iq
from twilix.base.myelement import MyElement
from twilix.jid import internJID

from .user import UserPresence, UserItemInfo
from .connect import ConnectPresence
from .admin import makeAdminQuery
    
class MultiChat(object):
    """
    Class implements multi chat user extension.
    """
    
    #signals
    user_available = object()
    user_unavailable = object()
    
    def __init__(self, dispatcher):
        """Setup global configuration"""
        self.dispatcher = dispatcher
        
    def init(self):
        """Makes some initialization actions"""
        self.roster = {}
        self.dispatcher.registerHandler((UserPresence, self))
        
    def enter_room(self, presence, room_jid, nickname):
        """
        Sends 'available'-type presence which allows client to enter the room.
        Fails if user already in room.
        
        :param room_jid: JID of room-conference
        :param nickname: string-type client's nickname in conference
        :param status: string-type client's status message
        
        """
        reciever = internJID(room_jid)
        
        assert reciever.bare() not in self.roster, 'already in room'
        
        reciever.resource = nickname
 
        presence = MyElement.makeFromElement(presence)
        presence = Presence.createFromElement(presence)
 
        presence.to = reciever
        presence.from_ = self.dispatcher.myjid
        
        msg = ConnectPresence(parent=presence)
        
        self.roster[reciever.bare()] = []
        
        self.dispatcher.send(msg.parent)
        
    def leave_room(self, presence, room_jid, nickname):
        """
        Sends 'unavailable'-type presence which leaves client from the room.
        Fails if user not in room.
        
        :param room_jid: JID of room-conference
        :param nickname: string-type client's nickname in conference
        
        """
        reciever = internJID(room_jid)
        
        assert reciever.bare() in self.roster, 'not in room'
        
        reciever.resource = nickname
        
        presence = MyElement.makeFromElement(presence)
        presence = Presence.createFromElement(presence)
        
        presence.to = reciever
        presence.from_ = self.dispatcher.myjid
        presence.type_ = 'unavailable'
        
        msg = ConnectPresence(parent=presence)
        
        self.dispatcher.send(msg.parent)
        
        del self.roster[reciever.bare()]
        
    def set_affiliation(self, room_jid, jid, affiliation, reason=None):
        """
        Sends query for changing user's affiliation to room jid.
        Uses mostly of chat administrators.
        
        :param room_jid: JID of room-conference
        :param jid: JID of user
        :param affiliation: value of new user's affiliation
        :param reason: string-type argument with reason of affiliation changing
                       (default None)
        
        """
        iq = Iq(type_='set', to=room_jid, from_=self.dispatcher.myjid)
        i = UserItemInfo(jid=internJID(jid), affiliation=affiliation, reason=reason)
        return makeAdminQuery(i, iq, self.dispatcher)
        
    def set_role(self, room_jid, nick, role, reason=None):
        """
        Sends query for changing user's role in chat to room jid.
        Uses mostly of chat administrators.
        
        :param room_jid: JID of room-conference

        :param nick: string-type user's nickname

        :param role: value of new user's role

        :param reason: string-type argument with reason of role changing
                      (default None)
        
        """
        iq = Iq(type_='set', to=room_jid, from_=self.dispatcher.myjid)
        i = UserItemInfo(nick=nick, role=role, reason=reason)
        return makeAdminQuery(i, iq, self.dispatcher) 
        
    def get_list(self, room_jid, affiliation=None, role=None):
        """
        Sends query for receiving list of all users with fixed
        value of role or affiliation in room.
        Uses mostly of chat administrators.
        
        :param room_jid: JID of room-conference

        :param role: value of role for users will be filtered (default None)

        :param affiliation: value of affiliation for users will be filtered
                            (default None)
        
        """
        iq = Iq(type_='get', to=room_jid, from_=self.dispatcher.myjid)
        i = UserItemInfo(role=role, affiliation=affiliation)
        return makeAdminQuery(i, iq, self.dispatcher)

