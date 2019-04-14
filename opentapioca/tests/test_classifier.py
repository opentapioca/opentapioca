
import unittest
import os
import pytest
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.tagger import Tagger
from opentapioca.classifier import SimpleTagClassifier
from opentapioca.indexingprofile import IndexingProfile
from opentapioca.readers.dumpreader import WikidataDumpReader
from opentapioca.tag import Tag
from opentapioca.mention import Mention
from pynif import NIFCollection
from opentapioca.taggerfactory import CollectionAlreadyExists

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
        
        # Load dummy profile
        cls.profile = IndexingProfile.load(os.path.join(cls.testdir, 'data/all_items_profile.json'))
        
        # Setup solr index (TODO delete this) and tagger
        cls.tf = TaggerFactory()
        cls.collection_name = 'wd_test_collection'
        try:
            cls.tf.create_collection(cls.collection_name)
        except CollectionAlreadyExists:
            pass
        cls.tf.index_stream(cls.collection_name,
                            WikidataDumpReader(os.path.join(cls.testdir, 'data/sample_wikidata_items.json.bz2')),
                            cls.profile)
        cls.tagger = Tagger(cls.collection_name, cls.bow, cls.graph)
        
        # Load NIF dataset
        cls.nif = NIFCollection.load(os.path.join(cls.testdir, 'data/five-affiliations.ttl'))
        
        cls.classifier = SimpleTagClassifier(cls.tagger, max_similarity_distance=10, similarity_smoothing=2)
        
    @classmethod
    def tearDownClass(cls):
        cls.tf.delete_collection(cls.collection_name)
        
    def test_tag_dataset(self):
        docid_to_mentions = self.classifier.tag_dataset(self.nif)
        self.assertEqual(len(docid_to_mentions['file:///tmp/five-affiliations.ttl/1']), 2)
             
    def test_compute_similarities(self):
        sentence = 'Vanuatu is very very far appart from Sweden, an EU member'
        mentions = [
            Mention(phrase='Vanuatu', start=0, end=7, tags=[Tag(id='Q686')], log_likelihood=1),
            Mention(phrase='Sweden', start=37, end=43, tags=[Tag(id='Q34', edges=[458])], log_likelihood=1),
            Mention(phrase='EU', start=48, end=50, tags=[Tag(id='Q458')], log_likelihood=1),
        ]
        for mention in mentions:
            self.classifier.compute_similarities(mention, mentions)
            
        id1 = (0, 7, 'Q686')
        id2 = (37, 43, 'Q34')
        id3 = (48, 50, 'Q458')
        expected_similarities = [
            [{'tag': id1, 'score': 1.0}],
            [{'tag': id2, 'score': pytest.approx(0.57, abs=0.01)}, {'tag': id3, 'score': pytest.approx(0.42, abs=0.01)}],
            [{'tag': id3, 'score': pytest.approx(0.57, abs=0.01)}, {'tag': id2, 'score': pytest.approx(0.42, abs=0.01)}]
        ]
            
        self.assertEqual(expected_similarities, [mention.tags[0].similarities for mention in mentions])
        

        
