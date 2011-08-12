from pydispatch import dispatcher

from twilix.stanzas import Iq, Query, Presence
from twilix.base import WrongElement, VElement

from twilix import fields

class RosterItem(VElement):
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
        return self._nick

    def addGroup(self, group_name):
        if not group_name in self._groups:
            self.groups = list(self._groups) + [group_name]
            return True

    def removeGroup(self, group_name):
        if group_name in self._groups:
            _groups = list(self._groups)
            _groups.remove(group_name)
            self.groups = _groups
            return True

    def __unicode__(self):
        return '<RosterItem %s %s, subscription %s>' % \
               (self.jid, self.nick, self.subscription)

    def __repr__(self):
        return self.__unicode__()

class RosterQuery(Query):
    elementUri = 'jabber:iq:roster'

    items = fields.ElementNode(RosterItem, listed=True, unique=True,
                               required=False)

    def __init__(self, **kwargs):
        super(RosterQuery, self).__init__(**kwargs)

    def setHandler(self):
        self.iq.from_ = None
        self.host.updateRoster(self)
        return self.iq.makeResult()

    def getHandler(self):
        self.iq.from_ = None
        return self.iq.makeError('cancel', 'not-acceptable')

class RosterPresence(Presence):
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
        self.dispatcher = dispatcher
        self.items = []
        self.mypresence = mypresence

    def init(self):
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
        assert self is sender
        if self.mypresence is not None:
            self.updatePresence(self.mypresence)

    def updatePresence(self, presence, send=True):
        self.mypresence = presence
        if send:
            self.dispatcher.send(presence)
        
    def gotRoster(self, query):
        self.items = list(query.items)
        dispatcher.send(self.roster_got, self)

    def addItem(self, item):
        query = RosterQuery(self, parent=Iq(type_='set'))
        query.link(item)
        self.dispatcher.send(query.iq)

    def removeItem(self, item):
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
