"""
Defines the User Location (XEP-0080) payload to be used in PEP.
"""


from twilix.base.velement import VElement
from twilix.fields import FloatNode as F, StringNode as S
from twilix.fields import DateTimeNode
from twilix.base.exceptions import ElementParseError

class GeolocEntry(VElement):
    elementName = 'geoloc'
    elementUri = 'http://jabber.org/protocol/geoloc'

    accuracy = F('accuracy', required=False)
    alt = F('alt', required=False)
    area = F('area', required=False)
    bearing = F('bearing', required=False)
    building = S('building', required=False)
    country = S('country', required=False)
    country_code = S('countrycode', required=False)
    datum = S('datum', required=False)
    description = S('description', required=False)
    error = F('error', required=False)
    floor = S('floor', required=False)
    lat = F('lat', required=False)
    locality = S('locality', required=False)
    lon = F('lon', required=False)
    postalcode = S('postalcode', required=False)
    region = S('region', required=False)
    room = S('room', required=False)
    speed = F('speed', required=False)
    street = S('street', required=False)
    text = S('text', required=False)
    timestamp = DateTimeNode('timestemp', required=False)
    uri_ = S('uri', required=False)

    def clean(self):
        vs = filter(None, [getattr(self, v, None) for v in ('lat', 'lon')])
        l = len(vs)
        if l == 1:
            raise ElementParseError

