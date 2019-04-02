
import unittest
import requests
import os
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.taggerfactory import CollectionAlreadyExists
from opentapioca.tagger import Tagger

class TaggerFactoryTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        cls.solr_endpoint = 'http://localhost:8983/solr/'
        cls.tf = TaggerFactory(cls.solr_endpoint)
        # Skip entire test if solr is not running
        try:
            r = requests.get(cls.solr_endpoint)
        except requests.exceptions.RequestException:
            raise unittest.SkipTest('Solr is not running')
        
    def test_create_collection(self):
        try:
            self.tf.create_collection('test_collection')
            with self.assertRaises(CollectionAlreadyExists):
                self.tf.create_collection('test_collection')
        finally:
            self.tf.delete_collection('test_collection')
            pass
            
    def test_index_wd_dump(self):
        try:
            self.tf.delete_collection('wd_test_collection')
        except requests.exceptions.RequestException:
            pass
        try:
            self.tf.create_collection('wd_test_collection')
            self.tf.index_wd_dump('wd_test_collection',
                                  os.path.join(self.testdir, 'data/sample_wikidata_items.json.bz2'),
                                  batch_size=20,commit_time=2)
            
            r = requests.post(self.solr_endpoint+'wd_test_collection/tag',
                              params={'overlaps':'NO_SUB',
                                      'tagsLimit':5000,
                                      'fl':'id,label,aliases,desc,grid,nb_statements,nb_sitelinks,edges,type',
                                      'wt':'json',
                                      'indent':'on',
                                      },
                              headers ={'Content-Type':'text/plain'},
                              data="I live in Vanuatu".encode('utf-8'))
            resp = r.json()
            self.assertEqual(['startOffset', 10, 'endOffset', 17, 'ids', ['Q686']], resp['tags'][0])
        finally:
            self.tf.delete_collection('wd_test_collection')
            pass
            
            
