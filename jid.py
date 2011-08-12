import copy

from twisted.words.protocols.jabber.jid import JID, InvalidFormat

class MyJID(JID):
    @property
    def is_bare(self):
        return self.resource is None

    def bare(self):
        new = copy.copy(self)
        new.resource = None
        return new

    def __unicode__(self):
        r = self.host
        if self.user:
            r = self.user + '@' + r
        if self.resource:
            r += '/' + self.resource
        return r

__internJIDs = {}
 
def internJID(jidstring):
    if jidstring in __internJIDs:
        j = __internJIDs[jidstring]
    else:
        j = MyJID(jidstring)
        __internJIDs[jidstring] = j
    j = copy.copy(j)
    return j
