import unittest

from twilix.stanzas import Iq, Query

class TestMyElement(unittest.TestCase):
    
    def testLink(self):
        class RIq(Iq):
            result_class = 'result_iq_class'
            error_class = 'error_iq_class'

        class MyQuery(Query):
            elementName = 'test-query'
            elementUri = 'test-uri'

        class MyQueryWithResults(MyQuery):
            result_class = 'result_query_class'
            error_class = 'error_query_class'

        iq = RIq(type_='set')
        iq.link(MyQuery())

        self.assertEqual(iq.result_class, 'result_iq_class')
        self.assertEqual(iq.error_class, 'error_iq_class')
        self.assertEqual(len(iq.children), 1)

        iq.link(MyQueryWithResults())
        self.assertEqual(iq.result_class, 'result_query_class')
        self.assertEqual(iq.error_class, 'error_query_class')
        self.assertEqual(len(iq.children), 1)

    # XXX: more tests here
