from twisted.words.xish.domish import Element

class ElementParseError(Exception):
    """Rises when attribute is required and value is None."""
    pass

class WrongElement(Exception):
    """Rises when there is an attempt to create an element from improper."""
    pass

class EmptyStanza(object):
    """Stanza without any attributes."""
    pass

class EmptyElement(object):
    """Element without value"""
    pass

class BreakStanza(object):
    pass

class MyElement(Element):
    """
    Extend class Element from twisted.words.xish.domish.
    """
    
    attributesProps = {}
    nodesProps = {}
    
    @classmethod
    def makeFromElement(cls, el):
        """
        Class method. Make copy of element.
        
        :param el: element to copy
        :type el: Element
        
        :returns:  myel -- copy of element el
        
        """
        myel = cls((el.uri, el.name))
        myel.attributes = el.attributes
        for c in el.children:
            if isinstance(c, (str, unicode)):
                myel.children.append(c)
            else:
                myel.children.append(cls.makeFromElement(c))
        return myel

    @classmethod
    def createFromElement(cls, el, host=None, **kwargs):
        """
        Class method. Make class instance of element
        if it's suits to class.
        
        :returns: class instance with host and kwargs of element
        
        :rises: WrongElement   
        """
        if isinstance(cls.elementUri, (tuple, list)):
            if el.uri not in cls.elementUri:
                raise WrongElement
        elif el is None:
            raise WrongElement
        else:
            if cls.elementUri is not None and el.uri != cls.elementUri:
                raise WrongElement
        if cls.elementName is not None and el.name != cls.elementName:
            raise WrongElement
        for name, attr in cls.attributesProps.items():
            kwargs[name] = el.attributes.get(attr.xmlattr, None)
        for name, attr in cls.nodesProps.items():
            kwargs[name] = attr.get_from_el(el)
        r = cls(host=host, **kwargs)
        r.children = el.children
        return r

    @classmethod
    def topClass(cls):
        """
        Class method. 
        Return top class in class hierarchy.
        
        :returns:  
            cls if class have not parent class
            
            top class of parent class otherwise
            
        """
        parent = getattr(cls, 'parentClass', None)
        if parent:
            return parent.topClass()
        return cls

    def validate(self):
        """Validate all attributes."""
        parent = getattr(self, 'parent', None)
        if parent is not None:
            parent.validate()
        for name, attr in self.__class__.attributesProps.items():
            getattr(self, name, None)
        for name, attr in self.__class__.nodesProps.items():
            getattr(self, name, None)

    def __getattr__(self, name):  #XXX: refactor?
        """Overrides __getattr__ method.
        
        Return valid attribute or not listed node if it's exist.
        
        Return list of valid childrens of node if it's listed.
        
        Return function adder or remover if it's required and node is
        listed.
        
        Call __getattr__ method of super class otherwise.         
        """
        need_adder = False
        need_remover = False
        if name.startswith('add'):
            name = name[3:].lower()
            need_adder = True
        elif name.startswith('remove'):
            name = name[6:].lower()
            need_remover = True
        attr = self.attributesProps.get(name, None)
        node = self.nodesProps.get(name, None)
        if attr and not need_adder:
            return self._validate(name, attr, attr.get_from_el(self))
        elif node:
            if need_adder and node.listed:
                def adder(value):
                    if not isinstance(value, (tuple, list)):
                        values = (value,)
                    else:
                        values = value
                    r = False
                    node = self.nodesProps.get(name)
                    old = getattr(self, name, ())
                    for value in values:
                        if node.unique and value in old:
                            continue
                        r = True
                        content = self._validate(name, node, value)
                        if isinstance(content, MyElement):
                            self.addChild(content)
                        else:
                            n = MyElement((None, xmlnode))
                            node.addChild(unicode(content))
                            self.addChild(n)
                    return r
                return adder
            elif need_remover and listed:   #XXX: node.listed?
                def remover(value):
                    if not isinstance(value, (tuple, list)):
                        values = [value,]
                    else:
                        values = list(value)
                    old_values = list(getattr(self, attr, ()))
                    r = False
                    for value in values:
                        while value in old_values:
                            old_values.remove(value)
                            r = True
                    setattr(self, attr, old_values)
                    return r
                return remover

            elif (need_adder or need_remover):
                return
            if node.listed:
                return [self._validate(name, node, v) \
                        for v in node.get_from_el(self)]
            else:
                return self._validate(name, node, node.get_from_el(self))
        elif not name.startswith('clean_'):
            return super(MyElement, self).__getattr__(name)

    def _validate(self, name, attr, value, setter=False):
        """
        Call cleaning function to attributes value according to the
        name and setter. 
        Return clean value.
        
        :param name: name of attribute
        
        :param attr: attribute
        
        :param value: value of attribute
        
        :param setter: using of setter
        
        :returns: value - clean value
        
        :rises: ElementParseError
        """
        if not setter:
            value = attr.clean(value)
        if setter and hasattr(attr, 'clean_set'):
            value = attr.clean_set(value)
        if not setter:
            nvalidator = getattr(self, 'clean_%s' % name, None)
            if nvalidator is not None:
                value = nvalidator(value)
        if value is None:
            if attr.required:
                raise ElementParseError, u'attr %s is required' % attr
        return value

    def __setattr__(self, name, value):
        """
        Overrides __setattr__ method.
        
        Set new value to attribute with name if it's exist. 
        
        Call __setattr__ method of super class otherwise.
        """
        attr = self.attributesProps.get(name, None)
        node = self.nodesProps.get(name, None)
        if attr:
            value = self._validate(name, attr, value, setter=True)
            self.cleanAttribute(attr.xmlattr)
            if value is not None:
                self.attributes[attr.xmlattr] = unicode(value)
        elif node:
            if value is None and node.required:
                raise ElementParseError, 'required node %s is not specified' % name
            self.removeChilds(name=node.xmlnode)
            if not node.listed or value is None:
                values = (value,)
            else:
                values = value
            for value in values:
                content = self._validate(name, node, value, setter=True)
                if isinstance(content, MyElement):
                    self.addChild(content)
                elif isinstance(content, EmptyElement) or content is None:
                    pass
                else:
                    n = MyElement((None, node.xmlnode))
                    n.addChild(unicode(content))
                    self.addChild(n)
        else:
            super(MyElement, self).__setattr__(name, value)

    def topElement(self):
        """
        Return top element in elements hierarchy.
        
        :returns:  
            self if instance have not parent elements
            
            top element of parent elemen otherwise
            
        """
        parent = getattr(self, 'parent', None)
        if parent:
            return parent.topElement()
        return self

    def _content_get(self):
        """
        Getter for property descriptor.
        Return content.
        :returns: unicode content
        :rises: ValueError
        """
        r = u''
        for c in self.children:
            if not isinstance(c, (unicode, str)):
                raise ValueError
            r += c
        return r

    def _content_set(self, value):
        """
        Setter for property descriptor.
        Remove old content.
        Set value as content.        
        """
        self.removeChilds()
        self.children.append(unicode(value))
    content = property(_content_get, _content_set)

    def addElement(self, name, defaultUri=None, content=None):
        """
        Append element to childrens. 
        Return element with specified name, Uri and content.
        """
        result = None
        if isinstance(name, type(())):    #XXX: tuple?
            if defaultUri is None:
                defaultUri = name[0]
            self.children.append(MyElement(name, defaultUri))
        else:
            if defaultUri is None:
                defaultUri = self.defaultUri
            self.children.append(MyElement((defaultUri, name), defaultUri))

        result = self.children[-1]
        result.parent = self

        if content:
            result.children.append(content)

        return result

    def cleanAttribute(self, attrib):
        """Delete attribute if it's exist."""
        if self.hasAttribute(attrib):
            del self.attributes[attrib]

    def removeChilds(self, name=None, uri=None, element=None):
        """
        Remove all content and child elements appropriate 
        to name-uri pair.
        """
        if element is not None:
            name = element.elementName
            uri = getattr(element, 'elementUri', None)
        children = []
        for el in self.children:
            if not isinstance(el, (str, unicode)) and \
               not (el.name == name and (uri is None or el.uri == uri)):
                children.append(el)
        self.children = children

    def getFirstChild(self, name=None):
        """Return first child element with name if exist."""
        el = [e for e in self.children if not isinstance(e, (str, unicode)) \
              and e.name == name]
        if el:
            return el[0]

    def getFirstChildContent(self, name=None):
        """Return content of first child element with name if exist."""
        el = self.getFirstChild(name)
        if el is not None:
            return el.content

    def link(self, el, unique=True):
        """
        Replace child element with the same name and uri as element
        if uniqueness is required or just add element.
        """
        if unique:
            self.removeChilds(el.name, el.uri)
        self.addChild(el)

def get_declared_fields(bases, attrs):
    from twilix import fields
    attr_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.AttributeProp)]
    node_fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
                    attrs.items() if isinstance(obj, fields.NodeProp)]
    for base in bases[::-1]:
        if hasattr(base, 'attributesProps'):
            attr_fields = base.attributesProps.items() + attr_fields
        if hasattr(base, 'nodesProps'):
            node_fields = base.nodesProps.items() + node_fields
    return dict(attr_fields), dict(node_fields)

class DeclarativeFieldsMetaClass(type):
    def __new__(cls, name, bases, attrs):
        attrs['attributesProps'], attrs['nodesProps'] = \
              get_declared_fields(bases, attrs)
        new_class = super(DeclarativeFieldsMetaClass, cls).__new__(cls, name,
                                                                bases, attrs)
        return new_class

class VElement(MyElement):
    elementName = None
    elementUri = None
    elementPrefixes = {}

    __metaclass__ = DeclarativeFieldsMetaClass

    def __init__(self, **kwargs):
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

