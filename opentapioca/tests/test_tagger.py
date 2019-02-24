import unittest
import os
from opentapioca.tagger import Tagger
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.taggerfactory import TaggerFactory

class TaggerTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        super(TaggerTest, cls).tearDownClass()
        testdir = os.path.dirname(os.path.abspath(__file__))
        
        # Load dummy bow
        bow_fname = os.path.join(testdir, 'data/sample_bow.pkl')
        cls.bow = BOWLanguageModel()
        cls.bow.load(bow_fname)
        
        # Load dummy graph
        graph_fname = os.path.join(testdir, 'data/sample_wikidata_items.npz')
        pagerank_fname = os.path.join(testdir, 'data/sample_wikidata_items.pgrank.npy')
        cls.graph = WikidataGraph()
        cls.graph.load_from_matrix(graph_fname)
        cls.graph.load_pagerank(pagerank_fname)
        
        # Setup solr index
        cls.tf = TaggerFactory()
        cls.collection_name = 'wd_test_collection'
        cls.tf.create_collection(cls.collection_name)
        cls.tf.index_wd_dump('wd_test_collection',
                            os.path.join(testdir, 'data/sample_wikidata_items.json.bz2'))
        
    @classmethod
    def tearDownClass(cls):
        super(TaggerTest, cls).tearDownClass()
        cls.tf.delete_collection(cls.collection_name)
        
    def test_tag_and_rank(self):
        sut = Tagger(self.collection_name, self.bow, self.graph)
        mentions = sut.tag_and_rank('I live in Vanuatu')
        self.assertEqual(mentions[0].tags[0].id, 'Q686')
        
        
        