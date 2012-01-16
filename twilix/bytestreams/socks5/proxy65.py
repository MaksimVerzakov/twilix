"""
License

Copyright (C) 
2002-2004   Dave Smith (dizzyd@jabber.org)
2007-2008   Fabio Forno (xmpp:ff@jabber.bluendo.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

$Id: proxy65.py 34 2008-12-14 12:48:21Z fabio.forno@gmail.com $
"""

from twisted.internet import protocol, reactor
from twisted.python import usage, log
from twisted.words.protocols.jabber import component,jid
from twisted.application import app, service, internet
import sys, socket
import socks5

class XEP65Proxy(socks5.SOCKSv5):
    def __init__(self, host):
        socks5.SOCKSv5.__init__(self)
        self.host = host
        self.supportedAuthMechs = [socks5.AUTHMECH_ANON]
        self.supportedAddrs = [socks5.ADDR_DOMAINNAME]
        self.enabledCommands = [socks5.CMD_CONNECT]
        self.addr = ""

    def stopProducing(self):
        self.transport.loseConnection()

    def pauseProducing(self):
        self.transport.stopReading()

    def resumeProducing(self):
        self.transport.startReading()

    # ---------------------------------------------
    # SOCKSv5 subclass
    # ---------------------------------------------    
    def connectRequested(self, addr, port):
        # Check for special connect to the namespace -- this signifies that the client
        # is just checking to ensure it can connect to the streamhost
        if addr == "http://jabber.org/protocol/bytestreams":
            self.connectCompleted(addr, 0)
            self.transport.loseConnection()
            return
            
        # Save addr, for cleanup
        self.addr = addr
        
        # Check to see if the requested address is already
        # activated -- send an error if so
        if not self.host.connections.has_key(addr) or \
           self.host.connections[addr]['connection']:
            self.sendErrorReply(socks5.REPLY_CONN_NOT_ALLOWED)
            self.stopProducing()
            return

        self.pauseProducing()
        self.connectCompleted(addr, 0)
        self.host.connections[addr]['connection'] = self
        self.host.connections[addr]['established_deferred'].callback(None)

    def connectionLost(self, reason):
        self.host.unregisterSession(addr=self.addr)

    def dataReceived(self, buf):
        if self.state == socks5.STATE_READY:
            self.host.dataReceived(self.addr, buf)
        else:
            socks5.SOCKSv5.dataReceived(self, buf)

