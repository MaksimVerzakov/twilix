"""
Contains special functions to 
"""
import datetime
import re

class TzInfo(datetime.tzinfo):
    """
    Overrides datetime.tzinfo class.
    Contains info about time zone offset.
    """
    def __init__(self, minutes=0):
        """Set time zone offset in minutes."""
        self.__minutes = minutes
        self.__name = str(self.__minutes / 60.)
    
    def utcoffset(self, dt):
        """Return the offset set at initialization."""
        return datetime.timedelta(minutes=self.__minutes)

    def tzname(self, dt):
        """Return name."""
        return self.__name

    def dst(self, dt):
        """Return zero time zone offset."""
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

