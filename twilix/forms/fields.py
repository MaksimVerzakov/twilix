from twilix.base.velement import VElement
from twilix.errors import NotAcceptableException
from twilix.base.exceptions import ElementParseError
from twilix import fields

class Option(VElement):
    elementName = 'option'

    label = fields.StringAttr('label', required=False)
    value = fields.StringNode('value')

class Field(VElement):
    elementName = 'field'
    fieldType = None # To be redefined in derived classes
    
    type_ = fields.StringAttr('type')
    label = fields.StringAttr('label', required=False)
    var = fields.StringAttr('var')

    required = fields.FlagNode('required', default=False, required=False)
    values = fields.StringNode('value', listed=True, required=False)
    options = fields.ElementNode(Option, listed=True, required=False)

    def __init__(self, value=None, *args, **kwargs):
        self.kwargs = kwargs
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

    def fclean(self, values):
        if self.kwargs.get('required') and not values:
            raise ElementParseError, "Form field %s %s is required" % \
                    (self.var, self.type_)
        return values

    def _get_value(self):
        return self.values
    def _set_value(self, value):
        self.values = value
    def _del_value(self, value):
        self.values = ()
    value = property(_get_value, _set_value, _del_value)

class MultilineField(Field):
    def _get_value(self):
        return u'\n'.join(self.values)
    def _set_value(self, value):
        self.values = value.splitlines()
    value = property(_get_value, _set_value)

class SingleField(Field):
    def _get_value(self):
        if self.values:
            return self.values[0]
        return None
    def _set_value(self, value):
        self.values = (value,)
    def _del_value(self):
        self.values = ()
    value = property(_get_value, _set_value, _del_value)

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

    def fclean(self, values):
        values = super(JidMultiField, self).fclean(values)
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

    def fclean(self, values):
        super(List, self).fclean(values)
        if not self.options:
            return values
        allowed_values = [o.value for o in self.options]
        wrong_items = [v for v in values if v not in allowed_values]
        if wrong_items:
            raise NotAcceptableException(
                "%s is not in options list" % (wrong_items,))
        return values

class ListSingleField(List, SingleField):
    fieldType = 'list-single'

    def fclean(self, value):
        return super(ListSingleField, self).fclean((value,))

class ListMultiField(List, Field):
    fieldType = 'list-multi'

