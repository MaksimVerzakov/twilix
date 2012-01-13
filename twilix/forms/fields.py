from twilix.base.velement import VElement
from twilix.errors import NotAcceptableException
from twilix.base.exceptions import ElementParseError
from twilix import fields

class Option(VElement):
    elementName = 'option'

    label = fields.StringAttr('label')
    value = fields.StringNode('value')

class Field(VElement):
    elementName = 'field'
    fieldType = None # To be redefined in derived classes
    
    type_ = fields.StringAttr('type')
    label = fields.StringAttr('label', required=False)
    var = fields.StringAttr('var')

    required = fields.FlagNode('required', default=False)
    values = fields.StringNode('value', listed=True)
    options = fields.ElementNode(Option, listed=True, required=False)

    def __init__(self, value=None, *args, **kwargs):
        super(Field, self).__init__(*args, **kwargs)
        self.type_ = self.fieldType
        self.value = value

    def prepare_to_submit(self):
        self.label = None
        self.options = ()
        self.required = None

    def restore_for_validation(self, kwargs):
        self.options = kwargs.get('options')

    def clean_type_(self, value):
        if value == self.fieldType:
            return value
        raise WrongElement

    @property
    def value(self):
        return self.values

    @value.setter
    def value(self, value):
        self.values = value

    @value.deleter
    def value(self, value):
        self.values = ()

    def __nonzero__(self):
        return bool(self.value)

class MultilineField(Field):
    @property
    def value(self):
        return u'\n'.join(self.values)

    @value.setter
    def value(self, value):
        self.values = value.splitlines()

class SingleField(Field):
    @property
    def value(self):
        if self.values:
            return self.values[0]
        return None

    @value.setter
    def value(self, value):
        self.values = (value,)

    @value.deleter
    def value(self):
        self.values = ()

class BooleanField(SingleField):
    fieldType = 'boolean'

    values = fields.BooleanNode('value', listed=True)

class FixedField(MultilineField):
    fieldType = 'fixed'

class HiddenField(SingleField):
    fieldType = 'hidden'

class JidSingleField(SingleField):
    fieldType = 'jid-single'

    values = fields.JidNode('value', listed=True)

class JidMultiField(Field):
    fieldType = 'jid-multi'

    values = fields.JidNode('value', listed=True)

    def clean_values_listed(self, values):
        d = {}
        for x in values:
            d[x] = 1
        return list(d.keys())

class TextMultiField(MultilineField):
    fieldType = 'text-multi'

class TextPrivateField(SingleField):
    fieldType = 'text-private'

class TextSingleField(SingleField):
    fieldType = 'text-single'

class List(object):

    def clean_values_listed(self, values):
        allowed_values = [o.value for o in self.options]
        wrong_items = [v for v in values if v not in allowed_values]
        if wrong_items:
            raise NotAcceptableException # Message here?
        return values

class ListSingleField(List, SingleField):
    fieldType = 'list-single'

class ListMultiField(List, Field):
    fieldType = 'list-multi'

