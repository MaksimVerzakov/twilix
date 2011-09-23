import unittest

from twilix import utils

class TestParser(unittest.TestCase):
    def test_parse_timestampt(self):
        info = (2003, 11, 12, 12, 12, 12)
        s = utils.parse_timestamp("%s-%s-%sT%s:%s:%s" % info)
        result = (s.year, s.month, s.day, s.hour, s.minute, s.second)
        self.assertEqual(result, info)
        self.assertEqual(utils.parse_timestamp("sss"), None)
        info = (2003, 11, 12, 12, 12, 12100)
        s = utils.parse_timestamp("%s-%s-%sT%s:%s:%s" % info)
        result = (s.year, s.month, s.day, s.hour, s.minute, s.second, s.microsecond)
        self.assertEqual(result, info)
