
import unittest
import os
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.tagger import Tagger
from opentapioca.classifier import SimpleTagClassifier
from pynif import NIFCollection

class ClassifierTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        
        # Load dummy bow
        bow_fname = os.path.join(cls.testdir, 'data/sample_bow.pkl')
        cls.bow = BOWLanguageModel()
        cls.bow.load(bow_fname)
        
        # Load dummy graph
        graph_fname = os.path.join(cls.testdir, 'data/sample_wikidata_items.npz')
        pagerank_fname = os.path.join(cls.testdir, 'data/sample_wikidata_items.pgrank.npy')
        cls.graph = WikidataGraph()
        cls.graph.load_from_matrix(graph_fname)
        cls.graph.load_pagerank(pagerank_fname)
        
        
        # Setup solr index (TODO delete this) and tagger
        cls.tf = TaggerFactory()
        cls.collection_name = 'wd_test_collection'
        cls.tf.create_collection(cls.collection_name)
        cls.tf.index_wd_dump(cls.collection_name,
                            os.path.join(cls.testdir, 'data/sample_wikidata_items.json.bz2'))
        cls.tagger = Tagger(cls.collection_name, cls.bow, cls.graph)
        
        # Load NIF dataset
        cls.nif = NIFCollection.load(os.path.join(cls.testdir, 'data/five-affiliations.ttl'))
        
    @classmethod
    def tearDownClass(cls):
        cls.tf.delete_collection(cls.collection_name)
        
    def test_tag_dataset(self):
        classifier = SimpleTagClassifier(self.tagger)
        docid_to_mentions = classifier.tag_dataset(self.nif)
        self.assertEqual(len(docid_to_mentions['file:///tmp/five-affiliations.ttl/1']), 2)

        