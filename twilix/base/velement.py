from twilix import fields
from myelement import MyElement

def get_declared_fields(bases, attrs):
    """
    Getter for metaclass.
    Make lists of tuples with field name and field class of attributes 
    and nodes.
    
    :param bases: list of parents.
    
    :param attrs: list of attributes.
    
    :returns: dictionaries of field_name/value pair for attributes and nodes.
    
    """
    
    attr_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.AttributeProp)]
    node_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.NodeProp)]

    # TODO: don't allow fields starts with _ also.
    for field_name, _ in attr_fields + node_fields:
        if hasattr(VElement, field_name):
            raise ValueError, "Can not construct element with the %s \
property since it is a predefined keyword" % (field_name,)

    for base in bases[::-1]:
        if hasattr(base, 'attributesProps'):
            attr_fields = base.attributesProps.items() + attr_fields
        if hasattr(base, 'nodesProps'):
            node_fields = base.nodesProps.items() + node_fields
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

        _descriptors = attrs.get('_descriptors')
        if not _descriptors:
            for base in bases[::-1]:
                _descriptors = getattr(base, '_descriptors', None)
                if _descriptors is not None:
                    break

        for descriptor in _descriptors:
            if attrs.has_key(descriptor):
                attrs['_%s' % (descriptor,)] = attrs.pop(descriptor)

        new_class = super(DeclarativeFieldsMetaClass, cls).__new__(cls, name,
                                                                bases, attrs)
        return new_class

class VElement(MyElement):
    """
    Base class for stanzas and other items.
    Uses DeclarativeFieldsMetaClass as metaclass to parse fields declarations
    and to collect them to the attributesProp and nodesProps dictionaries.

    VElement validated based on elementName which is an XML tag name,
    elementUri which is an XML namespace (could be a string or a iterable of
    strings which means that any of that namespaces are valid for this element)
    and based on it's attributes and nodes that declared by using fields.
    """
    elementName = None
    elementUri = None
    elementPrefixes = {}

    host = None
    parent = None
    localPrefixes = None
    uri = None
    name = None
    children = None
    attributes = None
    defaultUri = None
    parentClass = None
    result_class = None
    error_class = None
    isRequired = True
    dispatcher = None
    _descriptors = ('result_class', 'error_class', 'dispatcher')

    __metaclass__ = DeclarativeFieldsMetaClass

    def __init__(self, **kwargs):
        """Initialize VElement object. You can set any value for any element
        attribute here.
        
        For example::
            iq = Iq(type_='set', from_='me')
        """
        uri = kwargs.get('uri', None)
        name = kwargs.get('el_name', self.elementName)
        if uri is None and isinstance(self.elementUri, (str, unicode)):
            uri = self.elementUri
        super(VElement, self).__init__((uri, name),
                                       localPrefixes=self.elementPrefixes)
        self.host = kwargs.get('host', None)
        self.parent = kwargs.get('parent', None)
        try:
            self._dispatcher = kwargs['dispatcher']
        except KeyError:
            pass
        top = kwargs.get('top', None)
        if getattr(self.parentClass, 'parentClass', None) is None:
            if self.parent is None:
                self.parent = top
        elif self.parent is None and top is not None:
            self.parent = self.parentClass(top=top)
        if self.parent is not None:
            self.parent.link(self)
        for attr in self.attributesProps:
            value = kwargs.get(attr, None)
            if value is not None:
                setattr(self, attr, value)
        for attr, node in self.nodesProps.items():
            value = kwargs.get(attr, None)
            if value is not None or node.default is not None:
                setattr(self, attr, value)

    def __getattr__(self, key, *args, **kwargs):
        if key in self._descriptors:
            value = getattr(self, '_%s' % (key,), None)
            if value == 'self':
                value = self
            if value is not None and not self._links:
                return value
            for link in self._links:
                _value = getattr(link, key, None)
                if _value is not None:
                    return _value
            return value
        return super(VElement, self).__getattr__(key, *args, **kwargs)

    def __eq__(self, other):
        """
        Overrides comparison operator ==.
        :returns:
            False if elements ain't equal.
            
            True if elements are equal.
            
        """
        if isinstance(other, (str, unicode)):
            return False
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

    @property
    def iq(self):
        """Return valid iq when it's requested."""
        return self.topElement()

    def makeResult(self, *args, **kwargs):
        top = self.iq.makeResult()
        if getattr(self, '_result_class', None):
            result = self._result_class(top=top, *args, **kwargs)
        else:
            result = top
        return result
