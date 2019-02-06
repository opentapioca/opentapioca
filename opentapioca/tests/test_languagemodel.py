import unittest
from opentapioca.languagemodel import tokenize
from opentapioca.languagemodel import BOWLanguageModel

class BOWTest(unittest.TestCase):
    def test_tokenize(self):
        assert tokenize('invited speakers') == ['invited', 'speakers']
    
    def test_ingest(self):
        bow = BOWLanguageModel()
        bow.ingest(['the', 'invited', 'speaker'])
        bow.ingest(['the', 'speaker', 'of', 'the', 'house'])
        assert bow.word_count['speaker'] == 2
        assert bow.word_count['house'] == 1
        assert bow.total_count == 8
        ll = bow.log_likelihood('dear speaker')
        assert ll > -4.2 and ll < -4.1
