
import unittest
import os
import re
from opentapioca.dumpreader import WikidataDumpReader

class WikidataDumpReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        testdir = os.path.dirname(os.path.abspath(__file__))
        cls.dump_fname = os.path.join(testdir, 'data/sample_wikidata_items.json.bz2')
        
    def test_read_dump(self):
        count = 0
        entity_ids = re.compile(r'[QPL]\d+')
        with WikidataDumpReader(self.dump_fname) as reader:
            for item in reader:
                count += 1
                assert entity_ids.match(item.get('id')) is not None
        assert count == 100