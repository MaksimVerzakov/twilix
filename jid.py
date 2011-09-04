"""
Module extends the JID class from twisted library

"""

import copy

from twisted.words.protocols.jabber.jid import JID, InvalidFormat

class MyJID(JID):
    """Extends class JID"""
    @property
    def is_bare(self):
        """Checks for bare jid (without resourse part)"""
        return self.resource is None

    def bare(self):
        """Makes bare jid from current jid (without resourse part)"""
        new = copy.copy(self)
        new.resource = None
        return new

    def __unicode__(self):
        """Overrides unicode converter"""
        r = self.host
        if self.user:
            r = self.user + '@' + r
        if self.resource:
            r += '/' + self.resource
        return r

#buffer for recent string-to-jid conversations
__internJIDs = {}
 
def internJID(jidstring):
    """
    Creates and returns MyJID-type object from any jidstring 
    (with bufferization)
    """
    if jidstring in __internJIDs:
        j = __internJIDs[jidstring]
    else:
        j = MyJID(jidstring)
        __internJIDs[jidstring] = j
    j = copy.copy(j)
    return j
