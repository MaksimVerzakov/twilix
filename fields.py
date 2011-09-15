"""
Contains description of main attribute properties and node properties.
"""
import base64

from twilix.jid import internJID
from twilix.base import ElementParseError, MyElement, EmptyElement
from twilix.utils import parse_timestamp

class AttributeProp(object):
    """Base class for all attribute properties."""
    def __init__(self, xmlattr, required=True):
        self.required = required
        self.xmlattr = xmlattr

    def get_from_el(self, el):
        """
        Return required xml attribute from element.
        
        :returns:
            xml attribute from element.
            
            None if attribute isn't exist.
            
        """
        return el.attributes.get(self.xmlattr, None)

    def __unicode__(self):
        """Overrides __unicode__ method of object."""
        return u'AttributeProp %s' % self.xmlattr
        
class StringAttr(AttributeProp):
    """String attribute."""
    def clean(self, value):
        """
        Return value cast to unicode. 
        Raise ElementParseError if there's no value but it's required.
        
        :returns: value cast to unicode.
        
        :raises: ElementParseError.
        """
        if value is not None:
            return unicode(value)
        elif self.required:
            raise ElementParseError, u'%s is required' % self

    def clean_set(self, value):
        """Return value cast to unicode."""
        if value is not None:
            return unicode(value)

class JidAttr(StringAttr):
    """Jabber id Attribute."""
    def clean(self, value):
        """
        Call clean method of parent class to value.
        
        :returns:
            value cast to internJID if value isn't None or required.
        """
        value = super(JidAttr, self).clean(value)
        if value is not None or self.required:
            return internJID(value)

class BooleanAttr(StringAttr):
    """Boolean attribute."""
    def clean(self, value):
        """
        Call clean method of parent class.
        
        :returns:
            True if value is 'true'
            
            False otherwise
            
        """
        value = super(BooleanAttr, self).clean(value)
        if value == 'true': value = True
        else: value = False
        return value

    def clean_set(self, value):
        if value:
            return u'true'
        return u'false'

class NodeProp(object):
    """Base class for all node properties."""
    def __init__(self, xmlnode, required=True, listed=False, unique=False):
        self.xmlnode = xmlnode
        self.required = required
        self.listed = listed
        self.unique = unique

    def get_from_el(self, el):
        """
        Get all nodes from el which names is the same to xmlnode or just
        all nodes if xmlnod is None.
        
        :returns:
            list of relevant elements if node is listed.
            
            element otherwise.
        
        :raises:
            ElementParseError       
        """
        r = filter(lambda el: not isinstance(el, (str, unicode)) and \
                              (getattr(el, 'name', None) == self.xmlnode or \
                               self.xmlnode is None),
                   el.children)
        if not self.listed and len(r) > 1:
            raise ElementParseError, 'node %s is not list' % self.xmlnode
        if self.listed:
            return tuple(r)
        if r:
            return r[0]

    def clean(self, value):
        """Return value."""
        return value

    def __unicode__(self):
        """Overrides __unicode__ method of object."""
        return 'NodeProp %s' % self.xmlnode

class StringNode(NodeProp):
    """Used for nodes contains string."""
    def __init__(self, *args, **kwargs):
        """
        Initialize StringNode object.
        Get uri and call __init__ method of parent.
        """
        try:
            self.uri = kwargs.pop('uri')
        except KeyError:
            self.uri = None
        super(StringNode, self).__init__(*args, **kwargs)

    def clean(self, value):
        """
        Return value cast to unicode.
        
        :returns: value cast to unicode
        
        :raises: ElementParseError if value is None but required.
        """
        if value is not None:
            return unicode(value)
        elif self.required:
            raise ElementParseError, u"%s is required" % self

    def clean_set(self, value):
        """
        Return MyElement with value as content or EmptyElement if value
        is empty.
        
        :returns:
            MyElement with value as content.
            
            EmptyElement if value is empty.        
            
        """
        if value is None:
            return EmptyElement()
        r = MyElement((self.uri, self.xmlnode))
        r.content = unicode(value)
        return r

class DateTimeNode(StringNode):
    """Used for nodes containes date and time info."""
    def get_from_el(self, el):
        """Return date and time info from element in datetime format."""
        el = super(DateTimeNode, self).get_from_el(el)
        el = super(DateTimeNode, self).clean(el)
        if el:
            return parse_timestamp(el)

    def clean(self, value):
        """Overrides clean method of StringNode."""
        return value

    def clean_set(self, value):
        """
        Return element contains unicode string with date, time and utc
        offset.
        
        :returns:
            EmptyElement() if there's no value.
            
            MyElement contains unicode string with date, time and utc
            offset.
            
        """
        if not value:
            return EmptyElement()
        res = value.strftime("%Y-%m-%dT%H:%M:%S")
        minutes = 0
        if value.utcoffset():
            minutes = value.utcoffset().seconds / 60
        if minutes == 0:
            res += 'Z'
        else:
            hours = minutes / 60
            minutes = minutes - hours * 60
            if hours > 0: res += "+"
            res += "%s:%s" % (hours, minutes)
        return super(DateTimeNode, self).clean_set(res)

class FlagNode(NodeProp):
    """Used for flag nodes."""
    def get_from_el(self, el):
        """
        :returns:
           True if there's attribute in element with the same name as
           xmlnode.
           
           False otherwise.
           
        """
        els = [e for e in el.children \
               if getattr(e, 'name', None) == self.xmlnode]
        if els:
            return True
        return False

    def clean(self, value):
        """
        :returns:
            True if value is exist.
            
            False otherwise.
            
        """
        if value:
            return True
        else:
            return False

    def clean_set(self, value):
        """
        :returns:
            MyElement if value is exist.
            
            EmptyElement otherwise.
            
        """
        if value:
            return MyElement((None, self.xmlnode))
        return EmptyElement()

class IntegerNode(StringNode):
    """Used for nodes containes integer number."""
    def clean(self, value):
        """
        Call clean method of parents class to value.
        Return value cast to integer if it's possible.
        
        :returns:
            value cast to integer.
            
            None if there's ValueError.
            
        """
        value = super(IntegerNode, self).clean(value)
        if value is not None:
            try:
                res = int(value)
            except ValueError:
                res = None
            return res

class Base64Node(StringNode):
    """Used for nodes containes base64 data."""
    def clean(self, value):
        """
        Return value in base64 format if it's possible.
        :returns: value cast to base64.
        :raises: ElementParseError
        """
        value = super(Base64Node, self).clean(value)
        try:
            value = base64.b64decode(value)
        except TypeError:
            raise ElementParseError
        return value

    def clean_set(self, value):
        """Return MyElement with value cast to base64 as content."""
        if value is not None:
            r = MyElement((None, self.xmlnode))
            r.content = base64.b64encode(unicode(value))
            return r

class ElementNode(NodeProp):
    """Used for nodes containes element."""
    def __init__(self, *args, **kwargs):
        if isinstance(args[0], (str, unicode)):     
            args = args[1:]
        cls = args[0]
        if len(args) > 1:
            args = args[1:]
        else:
            args = ()
        super(ElementNode, self).__init__(cls.elementName, *args, **kwargs)
        self.cls = cls

    def get_from_el(self, el):
        """
        Return all elements with appropriate name and URI.
        
        :returns:
            tuple of elements if node is listed.
            
            element otherwise.
            
        """
        r = filter(lambda c_el: \
                    (self.cls.elementName is None or \
                     getattr(c_el, 'name', None) == self.cls.elementName) and \
                    (self.cls.elementUri is None or \
                     getattr(c_el, 'uri', None) == self.cls.elementUri),
                   el.children)
        # Too strictly... :(
        #if not self.listed and len(r) > 1:
        #    raise ElementParseError, 'node %s is not list' % \
        #           (self.cls.elementName or self.cls.elementUri,)
        if self.listed:
            return tuple(r)
        if r:
            return r[0]

    def clean(self, value):
        """Return element according to class with value."""
        if value is None:
            return                                 #XXX: EmptyElement()?
        return self.cls.createFromElement(value)

