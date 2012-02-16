"""
Contains description of main attribute properties and node properties.

That properties are used to describe an XML-schema of stanzas and child
elements easier. Then stanzas are validated by such schemas and transformed
into useful Python-objects.

Also, this classes make data transformation to internal Python types (e.g.
MyJID or datetime).

To do data validation and/or transformation fields should implement an clean
and clean_set methods and return transformed value or raise ElementParseError
if transformation impossible. The first one used for situations when data
received from a real XML and the second one for situations when data is set
with Python and needs to be converted to an XML compatible thing. Clean
methods must raise ElementParseError if element has no suitable value.
"""
import base64

from twilix.jid import internJID
from twilix.base.exceptions import ElementParseError
from twilix.base.myelement import MyElement, EmptyElement
from twilix.utils import parse_timestamp

class AttributeProp(object):
    """Base class for all attribute properties."""
    def __init__(self, xmlattr, required=True, default=None):
        self.required = required
        self.xmlattr = xmlattr
        self.default = None

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

class StringType(object):
    def to_python(self, value):
        if value is not None:
            return unicode(value)

    def clean(self, value):
        if not value and self.required:
            raise ElementParseError, u'%s is required' % self
        return value

    def clean_set(self, value):
        if value is not None:
            return unicode(value)

class IntegerType(StringType):
    """Used for nodes contain integer number."""
    def to_python(self, value):
        """
        Return value cast to integer if it's possible.
        
        :returns:
            value cast to integer.
            
            None if there's ValueError.
            
        """
        value = super(IntegerType, self).to_python(value)
        try:
            res = int(value)
        except (ValueError, TypeError):
            res = None
        return res

class FloatType(StringType):
    def to_python(self, value):
        value = super(FloatType, self).to_python(value)
        try:
            res = float(value)
        except (ValueError, TypeError):
            res = None
        return res

class DateTimeType(StringType):
    """Used for nodes contain date and time info."""

    def to_python(self, value):
        value = super(DateTimeType, self).to_python(value)
        if value:
            value = parse_timestamp(value)
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
        return super(DateTimeType, self).clean_set(res)

class IntegerAttr(IntegerType, AttributeProp):
    """Integer attribute."""

class FloatAttr(IntegerType, AttributeProp):
    """Float number attribute."""
        
class StringAttr(StringType, AttributeProp):
    """Plain string attribute."""

class DateTimeAttr(DateTimeType, AttributeProp):
    """Datetime attribute."""

class JidType(StringType):
    """Jabber id Type. Automatically convert a value to the
    MyJID instance"""
    def to_python(self, value):
        value = super(JidType, self).to_python(value)
        if value is not None:
            # XXX: Must raise ElementParseError if JID can't be converted
            return internJID(value)

class JidAttr(JidType, AttributeProp):
    pass

class BooleanType(StringType):
    """Boolean attribute."""
    def to_python(self, value):
        """
        Transform true/false values to the Python's bool.
        
        :returns:
            True if value is 'true'
            
            False otherwise
            
        """
        value = super(BooleanType, self).to_python(value)
        if value == 'true': value = True
        else: value = False
        return value

    def clean_set(self, value):
        if value:
            return u'true'
        return u'false'

class BooleanAttr(BooleanType, StringAttr):
    pass

class NodeProp(object):
    """Base class for all node properties."""
    def __init__(self, xmlnode, required=True, listed=False, unique=False,
                       default=None):
        self.xmlnode = xmlnode
        self.required = required
        self.listed = listed
        self.unique = unique
        self.default = default

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

    def to_python(self, value):
        return value

    def clean(self, value):
        return value

    def __unicode__(self):
        """Overrides __unicode__ method of object."""
        return 'NodeProp %s' % self.xmlnode

class StringNode(StringType, NodeProp):
    """Used for nodes contain string."""
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
        value = super(StringNode, self).clean_set(value)
        r = MyElement((self.uri, self.xmlnode))
        r.content = unicode(value)
        return r

class DateTimeNode(DateTimeType, StringNode):
    pass

class FlagNode(NodeProp):
    """Used for flag nodes, for example, <registered/> from the XEP-100"""
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

    def to_python(self, value):
        """

        :returns:
             True if value is exist.
             
             False otherwise.
             
        """
        return bool(value)

    def clean_set(self, value):
        """

        :returns:
             MyElement if value is exist.
            
             EmptyElement otherwise.
            
        """
        if value:
            return MyElement((None, self.xmlnode))
        return EmptyElement()

class Base64Node(StringNode):
    """Used for nodes contain base64 data."""
    def to_python(self, value):
        """
        Return value in base64 format if it's possible.
        
        :returns: value cast to base64.
        
        :raises: ElementParseError.
        
        """
        value = super(Base64Node, self).to_python(value)
        try:
            value = base64.b64decode(value)
        except TypeError:
            raise ElementParseError
        return value

    def clean_set(self, value):
        """Return MyElement with value cast to base64 as content."""
        if value is not None:
            r = MyElement((None, self.xmlnode))
            r.content = base64.b64encode(value)
            return r

class ElementNode(NodeProp):
    """Used for nodes contain another element."""
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
        # XXX: Too strictly... :(
        #if not self.listed and len(r) > 1:
        #    raise ElementParseError, 'node %s is not list' % \
        #           (self.cls.elementName or self.cls.elementUri,)
        if self.listed:
            return tuple(r)
        if r:
            return r[0]

    def to_python(self, value):
        """Return element according to class with value."""
        if value is None:
            return                                 #XXX: EmptyElement()?
        return self.cls.createFromElement(value)

    def clean_set(self, value):
        if isinstance(value, dict):
            return self.cls(**value)
        return value

class BooleanNode(BooleanType, StringNode):
    pass

class JidNode(JidType, StringNode):
    pass

class IntegerNode(IntegerType, NodeProp):
    pass

class FloatNode(FloatType, NodeProp):
    pass
