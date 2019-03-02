
import unittest
import os

class ClassifierTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        
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
        
        
        # Setup solr index (TODO delete this) and tagger
        cls.tf = TaggerFactory()
        cls.collection_name = 'wd_test_collection'
        cls.tf.create_collection(cls.collection_name)
        cls.tf.index_wd_dump(cls.collection_name,
                            os.path.join(testdir, 'data/sample_wikidata_items.json.bz2'))
        cls.tagger = Tagger(cls.collection_name, cls.bow, cls.graph)
        
        # Load NIF dataset
        cls.nif = NIFCollection.load(os.path.join(testdir, 'data/five-affiliations.ttl'))
        
    @classmethod
    def tearDownClass(cls):
        cls.tf.delete_collection(cls.collection_name)
        
    def test_tag_dataset(self):
        classifier = SimpleTagClassifier(self.tagger)
        docid_to_mentions = classifier.tag_dataset(self.nif)
        with open(os.path.join(testdir, 'data/docid_to_mentions.pklè'), 'wb') as f:
            dct = dict(self.__dict__.items())
            del dct['tagger']
            pickle.dump(dct, f)
        