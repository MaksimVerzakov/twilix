from twilix import fields
from myelement import MyElement

def get_declared_fields(bases, attrs):
    """
    Getter for metaclass.
    Make lists of tuples with field name and value of attributes 
    and nodes.
    
    :param bases: list of parents.
    
    :param attrs: list of attributes.
    
    :returns: dictionaries of field_name/value pair for attributes and nodes.
    
    """
    
    attr_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.AttributeProp)]
    node_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.NodeProp)]
    for base in bases[::-1]:
        if hasattr(base, 'attributesProps'):
            attr_fields = base.attributesProps.items() + attr_fields #XXX: extend?
        if hasattr(base, 'nodesProps'):
            node_fields = base.nodesProps.items() + node_fields   #XXX: extend?
    return dict(attr_fields), dict(node_fields)

class DeclarativeFieldsMetaClass(type):
    """
    Metaclass for VElement.
    Set get_declared_fields as getter for fields 'attributesProps' and
    'nodesProps'.
    """
    def __new__(cls, name, bases, attrs):
        attrs['attributesProps'], attrs['nodesProps'] = \
              get_declared_fields(bases, attrs)
        new_class = super(DeclarativeFieldsMetaClass, cls).__new__(cls, name,
                                                                bases, attrs)
        return new_class

class VElement(MyElement):
    """
    Base class for stanzas and other items.
    Uses DeclarativeFieldsMetaClass as metaclass.    
    """
    elementName = None
    elementUri = None
    elementPrefixes = {}

    __metaclass__ = DeclarativeFieldsMetaClass

    def __init__(self, **kwargs):
        """Initialize VElement object."""
        uri = kwargs.get('uri', None)
        name = kwargs.get('el_name', self.elementName)
        if uri is None and isinstance(self.elementUri, (str, unicode)):
            uri = self.elementUri
        super(VElement, self).__init__((uri, name),
                                       localPrefixes=self.elementPrefixes)
        self.host = kwargs.get('host', None)
        self.parent = kwargs.get('parent', None)
        if self.parent is not None:
            self.parent = self.parentClass.createFromElement(self.parent)
            self.parent.addChild(self)
        for attr in self.attributesProps:
            value = kwargs.get(attr, None)
            setattr(self, attr, value)
        for attr in self.nodesProps:
            value = kwargs.get(attr, None)
            setattr(self, attr, value)

    def __eq__(self, other):
        """
        Overrides comparison operator ==.
        :returns:
            False if elements ain't equal.
            
            True if elements are equal.
            
        """
        if self.uri != other.uri or self.name != other.name:
            return False
        for attr in self.attributesProps:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        for attr in self.nodesProps:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True

    def __ne__(self, other):
        """
        Overrides comparison operator !=.
        :returns: denial results of function __eq__
        """
        return not self.__eq__(other)

    @classmethod
    def ___validate(cls, el):
        """
        Class method.
        Returns el if it's instance of class and create element from el
        of required type.
        """
        if isinstance(el, cls):
            return el
        return cls.createFromElement(el)

