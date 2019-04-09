import unittest
import os
import requests
from opentapioca.tagger import Tagger
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.indexingprofile import IndexingProfile
from opentapioca.readers.dumpreader import WikidataDumpReader

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
        
        # Load indexing profile
        cls.profile = IndexingProfile.load(os.path.join(testdir, 'data/all_items_profile.json'))
        
        # Setup solr index
        cls.tf = TaggerFactory()
        cls.collection_name = 'wd_test_collection'
        try:
            cls.tf.delete_collection('wd_test_collection')
        except requests.exceptions.RequestException:
            pass
        cls.tf.create_collection(cls.collection_name)
        cls.tf.index_stream('wd_test_collection',
                            WikidataDumpReader(os.path.join(testdir, 'data/sample_wikidata_items.json.bz2')),
                            cls.profile)
        
        cls.sut = Tagger(cls.collection_name, cls.bow, cls.graph)
        
    @classmethod
    def tearDownClass(cls):
        super(TaggerTest, cls).tearDownClass()
        cls.tf.delete_collection(cls.collection_name)
        
    def test_tag_and_rank(self):
        mentions = self.sut.tag_and_rank('I live in Vanuatu')
        self.assertEqual(mentions[0].tags[0].id, 'Q686')
        
    def test_prune_mention(self):
        self.assertTrue(self.sut.prune_phrase('of'))
        self.assertTrue(self.sut.prune_phrase('1 1'))
        self.assertFalse(self.sut.prune_phrase('orcid'))
        self.assertFalse(self.sut.prune_phrase('75005'))
        self.assertFalse(self.sut.prune_phrase('UK'))
        
        
        