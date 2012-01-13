import unittest
from datetime import timedelta

from twilix import utils

class TestParser(unittest.TestCase):
    def test_parse_timestampt(self):
        info = (2003, 11, 12, 12, 12, 12)
        s = utils.parse_timestamp("%s-%s-%sT%s:%s:%s" % info)
        result = (s.year, s.month, s.day, s.hour, s.minute, s.second)
        self.assertEqual(result, info)
        
        self.assertEqual(utils.parse_timestamp("sss"), None)
        
        info = ('2003', '11', '12', '12', '12', 
                '12', '100000', '02', '30')
        s = utils.parse_timestamp("%s-%s-%sT%s:%s:%s.%s-%s:%s" % info)
        info = [t for t in info[:-2]] 
        result = [str(t) for t in s.timetuple()[:-3]] + \
                  [str(s.microsecond)]
        self.assertEqual(result, info)
        
        info = (7223, 99, 99, 99, 99, 99)
        s = utils.parse_timestamp("%s-%s-%sT%s:%s:%s" % info)
        self.assertEqual(s, None)

class TestTzInfo(unittest.TestCase):
    
    def setUp(self):
        self.min = 127
        self.tz = utils.TzInfo(self.min)
    
    def test_utcoffset(self):
        self.assertEqual(self.tz.utcoffset(1), 
                         timedelta(minutes=self.min))
    
    def test_tzname(self):
        self.assertEqual(self.tz.tzname(1), str(self.min / 60.))
    
    def test_dst(self):
        self.assertEqual(self.tz.dst(1), timedelta(0))
