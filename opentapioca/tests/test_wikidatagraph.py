import unittest
import os
from opentapioca.wikidatagraph import WikidataGraph

class WikidataGraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(WikidataGraphTest, cls).setUpClass()
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        
    def test_compile_unordered_dump(self):
        graph = WikidataGraph()
        with self.assertRaises(ValueError):
            graph.load_from_preprocessed_dump(os.path.join(self.testdir, 'data/sample_wikidata_items.unsorted.tsv'))
            
    def test_compile_dump(self):
        graph = WikidataGraph()
        graph.load_from_preprocessed_dump(os.path.join(self.testdir, 'data/sample_wikidata_items.tsv'))
        graph.mat.check_format()
        self.assertEqual(graph.shape, 3942)
        
    def test_compute_pagerank(self):
        graph = WikidataGraph()
        graph.load_from_matrix(os.path.join(self.testdir, 'data/sample_wikidata_items.npz'))
        graph.compute_pagerank()
        self.assertTrue(graph.get_pagerank('Q45') > 0.0003 and graph.get_pagerank('Q45') < 0.0004)