import unittest
import os
import json
from opentapioca.wditem import WikidataItemDocument

class WDItemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        testdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(testdir, 'data/Q30264236.json'), 'r') as f:
            cls.sample_json = json.loads(f.read())
            
    def test_parse(self):
        item = WikidataItemDocument(self.sample_json)
        assert item.get_nb_statements() == 9
        assert item.get_nb_sitelinks() == 0
        assert item.get_types() == ['Q31855']
        assert set(item.get_outgoing_edges()) == {31855, 148, 530471, 9384257, 185684}
        assert str(item) == '<WikidataItemDocument Q30264236>'