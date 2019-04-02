
import unittest
import requests
import os
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.taggerfactory import CollectionAlreadyExists
from opentapioca.indexingprofile import IndexingProfile
from opentapioca.tagger import Tagger
from opentapioca.readers.dumpreader import WikidataDumpReader

class TaggerFactoryTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        cls.solr_endpoint = 'http://localhost:8983/solr/'
        cls.tf = TaggerFactory(cls.solr_endpoint)
        
        # Load dummy profile
        cls.profile = IndexingProfile.load(os.path.join(cls.testdir, 'data/all_items_profile.json'))
        
        # Skip entire test if solr is not running
        try:
            r = requests.get(cls.solr_endpoint)
        except requests.exceptions.RequestException:
            raise unittest.SkipTest('Solr is not running')
        
    def setUp(self):
        try:
            self.tf.delete_collection('wd_test_collection')
        except requests.exceptions.RequestException:
            pass
        
    def test_create_collection(self):
        try:
            self.tf.create_collection('test_collection')
            with self.assertRaises(CollectionAlreadyExists):
                self.tf.create_collection('test_collection')
        finally:
            self.tf.delete_collection('test_collection')
            pass
        
    def tag_sentence(self, sentence):
        """
        Tags a given sentence in the test collection
        """
        r = requests.post(self.solr_endpoint+'wd_test_collection/tag',
                              params={'overlaps':'NO_SUB',
                                      'tagsLimit':5000,
                                      'fl':'id,label,aliases,desc,extra_aliases,nb_statements,nb_sitelinks,edges,types',
                                      'wt':'json',
                                      'indent':'on',
                                      },
                              headers ={'Content-Type':'text/plain'},
                              data=sentence.encode('utf-8')) 
        r.raise_for_status()
        return r.json()
     
    def test_index_dump(self):
        try:
            self.tf.create_collection('wd_test_collection')
            dump = WikidataDumpReader(os.path.join(self.testdir, 'data/sample_wikidata_items.json.bz2'))
            self.tf.index_stream('wd_test_collection',
                                  dump,
                                  self.profile,
                                  batch_size=20,
                                  commit_time=2)
            

            resp = self.tag_sentence("I live in Vanuatu")
            self.assertEqual(['startOffset', 10, 'endOffset', 17, 'ids', ['Q686']], resp['tags'][0])
        finally:
            self.tf.delete_collection('wd_test_collection')
        
    def test_index_stream(self):
        try:
            self.tf.create_collection('wd_test_collection')
            # We use a dump reader but this was actually obtained from a stream!   
            dump = WikidataDumpReader(os.path.join(self.testdir, 'data/short_stream.json.bz2'))
            self.tf.index_stream('wd_test_collection',
                                  dump,
                                  self.profile,
                                  batch_size=50,
                                  commit_time=2,
                                  delete_excluded=True)
            
            resp = self.tag_sentence("Yesterday I met Ryszard Adam Bobrowski.")
            self.assertEqual(['startOffset', 16, 'endOffset', 38, 'ids', ['Q24428424']], resp['tags'][0])
        finally:
            self.tf.delete_collection('wd_test_collection')
            