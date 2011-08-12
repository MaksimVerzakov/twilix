errorCodeMap = {
	"bad-request": 400,
	"conflict":	409,
	"feature-not-implemented": 501,
	"forbidden": 403,
	"gone":	302,
	"internal-server-error": 500,
	"item-not-found": 404,
	"jid-malformed": 400,
	"not-acceptable": 406,
	"not-allowed": 405,
	"not-authorized": 401,
	"payment-required":	402,
	"recipient-unavailable": 404,
	"redirect": 302,
	"registration-required": 407,
	"remote-server-not-found": 404,
	"remote-server-timeout": 504,
	"resource-constraint": 500,
	"service-unavailable": 503,
	"subscription-required": 407,
	"undefined-condition": 500,
	"unexpected-request": 400
}

import datetime
import re

class TzInfo(datetime.tzinfo):
    def __init__(self, minutes=0):
        self.__minutes = minutes
        self.__name = str(self.__minutes / 60.)
    
    def utcoffset(self, dt):
        return datetime.timedelta(minutes=self.__minutes)

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)

def parse_timestamp(s):
    """Returns (datetime, tz offset in minutes) or (None, None)."""
    m = re.match(""" ^
    (?P<year>-?[0-9]{4}) - (?P<month>[0-9]{2}) - (?P<day>[0-9]{2})
    T (?P<hour>[0-9]{2}) : (?P<minute>[0-9]{2}) : (?P<second>[0-9]{2})
    (?P<microsecond>\.[0-9]{1,6})?
    (?P<tz>
      Z | (?P<tz_hr>[-+][0-9]{2}) : (?P<tz_min>[0-9]{2})
    )?
    $ """, s, re.X)
    if m is not None:
        values = m.groupdict()
    else:
        return None
    if values["tz"] in ("Z", None):
        tz = 0
    else:
        tz = int(values["tz_hr"]) * 60 + int(values["tz_min"])
    if values["microsecond"] is None:
        values["microsecond"] = 0
    else:
        values["microsecond"] = values["microsecond"][1:]
        values["microsecond"] += "0" * (6 - len(values["microsecond"]))
    values = dict((k, int(v)) for k, v in values.iteritems()
                  if not k.startswith("tz"))
    values['tzinfo'] = TzInfo(tz)
    try:
        return datetime.datetime(**values)
    except ValueError:
        pass
    return None

