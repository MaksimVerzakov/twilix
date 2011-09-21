

class iqEmul(object):
    
    uri=None
    attributes={}
    name='iq' 
    to='some_jid'
    children = []
    
    def makeResult(self):
        return self
        
    def link(self, content):
        self.children.append(content)
    
    def addChild(self, child):
        self.link(shild)
        
      
class dispatcherEmul(object):
    def __init__(self, myjid):
        self.myjid = myjid

class hostEmul(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
