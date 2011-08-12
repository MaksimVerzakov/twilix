import base64

from twilix.jid import internJID
from twilix.base import ElementParseError, WrongElement, MyElement, EmptyElement
from twilix.utils import parse_timestamp

class AttributeProp(object):
    def __init__(self, xmlattr, required=True):
        self.required = required
        self.xmlattr = xmlattr

    def get_from_el(self, el):
        return el.attributes.get(self.xmlattr, None)

    def __unicode__(self):
        return u'AttributeProp %s' % self.xmlattr
        
class StringAttr(AttributeProp):
    def clean(self, value):
        if value is not None:
            return unicode(value)
        elif self.required:
            raise ElementParseError, u'%s is required' % self

    def clean_set(self, value):
        if value is not None:
            return unicode(value)

class JidAttr(StringAttr):
    def clean(self, value):
        value = super(JidAttr, self).clean(value)
        if value is not None or self.required:
            return internJID(value)

class BooleanAttr(StringAttr):
    def clean(self, value):
        value = super(BooleanAttr, self).clean(value)
        if value == 'true': value = True
        else: value = False
        return value

    def clean_set(self, value):
        if value:
            return u'true'
        return u'false'

class NodeProp(object):
    def __init__(self, xmlnode, required=True, listed=False, unique=False):
        self.xmlnode = xmlnode
        self.required = required
        self.listed = listed
        self.unique = unique

    def get_from_el(self, el):
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
        return value

    def __unicode__(self):
        return 'NodeProp %s' % self.xmlnode

class StringNode(NodeProp):
    def __init__(self, *args, **kwargs):
        try:
            self.uri = kwargs.pop('uri')
        except KeyError:
            self.uri = None
        super(StringNode, self).__init__(*args, **kwargs)

    def clean(self, value):
        if value is not None:
            return unicode(value)
        elif self.required:
            raise ElementParseError, u"%s is required" % self

    def clean_set(self, value):
        if value is None:
            return EmptyElement()
        r = MyElement((self.uri, self.xmlnode))
        r.content = unicode(value)
        return r

class DateTimeNode(StringNode):
    def get_from_el(self, el):
        el = super(DateTimeNode, self).get_from_el(el)
        el = super(DateTimeNode, self).clean(el)
        if el:
            return parse_timestamp(el)

    def clean(self, value):
        return value

    def clean_set(self, value):
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
    def get_from_el(self, el):
        els = [e for e in el.children \
               if getattr(e, 'name', None) == self.xmlnode]
        if els:
            return True
        return False

    def clean(self, value):
        if value:
            return True
        else:
            return False

    def clean_set(self, value):
        if value:
            return MyElement((None, self.xmlnode))
        return EmptyElement()

class IntegerNode(StringNode):
    def clean(self, value):
        value = super(IntegerNode, self).clean(value)
        if value is not None:
            try:
                res = int(value)
            except ValueError:
                res = None
            return res

class Base64Node(StringNode):
    def clean(self, value):
        value = super(Base64Node, self).clean(value)
        try:
            value = base64.b64decode(value)
        except TypeError:
            raise ElementParseError
        return value

    def clean_set(self, value):
        if value is not None:
            r = MyElement((None, self.xmlnode))
            r.content = base64.b64encode(unicode(value))
            return r

class ElementNode(NodeProp):
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
        if value is None:
            return
        return self.cls.createFromElement(value)

