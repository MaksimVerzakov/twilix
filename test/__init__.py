

class iqEmul(object):
    
    uri=None
    attributes={}
    name='iq' 
    to='some_jid'
    children = []
    type_='type' 
    id = 'any_id'
    
    def makeResult(self):
        return self
        
    def link(self, content):
        self.children.append(content)
    
    def addChild(self, child):
        self.link(shild)
        
      
class dispatcherEmul(object):
    def __init__(self, myjid):
        self.myjid = myjid
        self._handlers = []
        self.data = []
    
    def registerHandler(self, handler):
        if not handler in self._handlers:
            self._handlers.append(handler)
            return True
    
    def send(self, data):
        self.data.append(data)

class hostEmul(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
