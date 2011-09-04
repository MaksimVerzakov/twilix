from pydispatch import dispatcher

from twilix.stanzas import Iq, Query, Presence
from twilix.base import WrongElement, VElement

from twilix import fields

class RosterItem(VElement):
    """
    Class for xml roster item node. Inheritor of VElement.
    
    Class has attributes-identificators for filter xml nodes, info 
    string-type fields and jid of roster element.
    
    """
    elementName = 'item'
    elementUri = 'jabber:iq:roster'

    jid = fields.JidAttr('jid')
    subscription = fields.StringAttr('subscription', required=False)
    ask = fields.StringAttr('ask', required=False)
    nick = fields.StringAttr('name', required=False)

    groups = fields.StringNode('group', required=False, listed=True,
                               unique=True)

    def __init__(self, **kwargs):
        super(RosterItem, self).__init__(**kwargs)
        self.presences = {}

    def is_online(self):
        return bool(self.presences)

    @property
    def nick(self):
        """Property for nickname attribute"""
        return self._nick

    def addGroup(self, group_name):
        """
        Adds new group in roster's list of groups
        
        :param group_name: name of new group.
        
        :returns: True if group was added else None if same group already exist.
        
        """
        if not group_name in self._groups:
            self.groups = list(self._groups) + [group_name]
            return True

    def removeGroup(self, group_name):
        """
        Deletes group from roster's list of groups
        
        :param group_name: name of deleted group.
        
        :returns: True if group was deleted else None if group not exist.
        
        """
        if group_name in self._groups:
            _groups = list(self._groups)
            _groups.remove(group_name)
            self.groups = _groups
            return True

    def __unicode__(self):
        """
        Unicode converter
        """
        return '<RosterItem %s %s, subscription %s>' % \
               (self.jid, self.nick, self.subscription)

    def __repr__(self):
        return self.__unicode__()

class RosterQuery(Query):
    """
    Class for xml roster queries. Inheritor of Query.
    
    Class attributes:
    
    elementUri -- identificator/filter for xml nodes
    
    items -- list of RosterItem instances
    
    """
    elementUri = 'jabber:iq:roster'

    items = fields.ElementNode(RosterItem, listed=True, unique=True,
                               required=False)

    def __init__(self, **kwargs):
        super(RosterQuery, self).__init__(**kwargs)

    def setHandler(self):
        """
        Method for handle set-type roster queries.
        Calls updateRoster method from host class.
        
        """
        self.iq.from_ = None
        self.host.updateRoster(self)
        return self.iq.makeResult()

    def getHandler(self):
        """
        Method for handle get-type roster queries.
        Not acceptable. Returns error stanza.
        
        """
        self.iq.from_ = None
        return self.iq.makeError('cancel', 'not-acceptable')

class RosterPresence(Presence):
    """
    Class for xml roster presence. Inheritor of Presence.
    Describes some handlers for other presences.
    Handlers send necessary signal with dispatcher (from pydispatch module)
    
    """
    def availableHandler(self):
        i = self.host.getItemByJid(self.from_)
        if i is None:
            return 
        resource = self.from_.resource
        changed_status = False
        if resource in i.presences:
            changed_status = True
        i.presences[self.from_.resource] = self
        if changed_status:
            dispatcher.send(self.host.resource_changed_status, self.host,
                            item=i, presence=self)
        elif len(i.presences) == 1:
            dispatcher.send(self.host.contact_available, self.host, item=i,
                            presence=self)
        if not changed_status:
            dispatcher.send(self.host.resource_available, self.host, item=i,
                            presence=self)

    def unavailableHandler(self):
        i = self.host.getItemByJid(self.from_)
        if i is not None and self.from_.resource in i.presences:
            del i.presences[self.from_.resource]
            if not i.presences:
                dispatcher.send(self.host.contact_unavailable, self.host,
                                item=i, presence=self)
            dispatcher.send(self.host.resource_unavailable, self.host, item=i,
                            presence=self)

    def errorHandler(self):
        self.unavailableHandler()

    def subscribeHandler(self):
        dispatcher.send(self.host.subscribe, self.host, presence=self)

    def subscribedHandler(self):
        dispatcher.send(self.host.subscribed, self.host, presence=self)

    def unsubscribeHandler(self):
        dispatcher.send(self.host.unsubscribe, self.host, presence=self)

    def unsubscribedHandler(self):
        dispatcher.send(self.host.unsubscribed, self.host, presence=self)

class Roster(object): #List of RosterItem
    # Signals
    """
    """
    roster_got = object()
    roster_item_added = object()
    roster_item_removed = object()
    contact_available = object()
    contact_unavailable = object()
    resource_available = object()
    resource_unavailable = object()
    resource_changed_status = object()

    subscribe = object()
    subscribed = object()
    unsubscribe = object()
    unsubscribed = object()

    def __init__(self, dispatcher, mypresence=None):
        """
        Sets some instance attributes
        
        :param dispatcher: dispatcher for send/receive stanzas
        
        """
        self.dispatcher = dispatcher
        self.items = []
        self.mypresence = mypresence

    def init(self):
        """
        Registers handlers for roster stanzas.
        Links roster_got signal with instance method.
        Sends roster get query.
        """
        self.dispatcher.registerHandler((RosterQuery, self))
        self.dispatcher.registerHandler((RosterPresence, self))
        dispatcher.connect(self._send_initial_presence, self.roster_got,
                           sender=self)
        iq = Iq(type_='get')
        query = RosterQuery(parent=iq)
        iq.result_class = RosterQuery
        iq.deferred.addCallback(self.gotRoster)
        self.dispatcher.send(iq)
    
    def _send_initial_presence(self, sender):
        """
        
        """
        assert self is sender
        if self.mypresence is not None:
            self.updatePresence(self.mypresence)

    def updatePresence(self, presence, send=True):
        """
        Sets value of mypresence and maybe send it
        
        :param presence: new value
        
        :param send: boolean, true for send new presence
        
        """
        self.mypresence = presence
        if send:
            self.dispatcher.send(presence)
        
    def gotRoster(self, query):
        """
        Saves roster items from query instance and send 
        roster_got signal to dispatcher (from pydispatch module)
        
        :param query: instance with roster items
        
        """
        self.items = list(query.items)
        dispatcher.send(self.roster_got, self)

    def addItem(self, item):
        """
        Sends set-type query for addition new item in roster
        
        :param item: value of new item
        
        """
        query = RosterQuery(self, parent=Iq(type_='set'))
        query.link(item)
        self.dispatcher.send(query.iq)

    def removeItem(self, item):
        """
        Sends set-type query for deletion item from roster
        
        :param item: value of removed item
        
        """
        item.subscription = 'remove'
        query = RosterQuery(self, parent=Iq(type_='set'))
        query.link(item)
        self.dispatcher.send(query.iq)

    def updateRoster(self, query):
        for i in query.items:
            if i.subscription == 'remove':
                self._removeItem(i)
            else:
                self._addItem(i)

    def getItemByJid(self, jid):
        r = None
        jid = jid.bare()
        for i in self.items:
            if jid == i.jid:
                r = i
        return r

    def _removeItem(self, item):
        i = self.getItemByJid(item.jid)
        if i is not None:
            self.items.remove(i)
            dispatcher.send(self.roster_item_removed, self, i)
            return True

    def _addItem(self, item):
        self._removeItem(item)
        self.items.append(item)
        dispatcher.send(self.roster_item_added, self, item)

    def getGroups(self):
        groups = []
        for i in self.items:
            for g in i.groups:
                if g not in groups:
                    groups.append(g)
        return groups

    def getGroupUsers(self, group):
        items = []
        for i in self.items:
            if group in i.groups:
                items.append(i)
        return items
