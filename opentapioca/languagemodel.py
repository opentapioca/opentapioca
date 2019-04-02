import pickle

import re
from unidecode import unidecode
from collections import defaultdict
from math import log
from opentapioca.readers.dumpreader import WikidataDumpReader

separator_re = re.compile(r'[,\-_/:;!?)]? [,\-_/:;!?(]?')

def tokenize(phrase):
    """
    Split a text into lists of words
    """
    words = [
        unidecode(word.strip())
        for word in separator_re.split(' '+phrase+' ')
    ]
    return [w for w in words if w]

class BOWLanguageModel(object):
    def __init__(self):
        self.total_count = 0
        self.word_count = defaultdict(int)
        self.smoothing = 1
        self.log_quotient = None
        self.threshold = 2

    def ingest(self, words):
        """
        Ingests a sequence of words in the language model
        """
        for word in words:
            self.word_count[word] += 1
        self.total_count += len(words)

    def ingest_phrases(self, phrases):
        """
        Given a list of strings (phrases), deduplicate all
        their words and ingest them.
        """
        word_set = set()
        for phrase in phrases:
            word_set |= set(tokenize(phrase))
        self.ingest(word_set)

    def log_likelihood(self, phrase):
        """
        Returns the log-likelihood of the phrase
        """
        words = tokenize(phrase)
        return sum(self._word_log_likelihood(word) for word in words)

    def _word_log_likelihood(self, word):
        """
        The log-likelihood for a single phrase
        """
        if self.log_quotient is None:
            self._update_log_quotient()
        return log(float(self.smoothing + self.word_count[word])) - self.log_quotient

    def _update_log_quotient(self):
        """
        Updates the precomputed quotient
        """
        self.log_quotient = log(self.smoothing*(1+len(self.word_count))+self.total_count)

    def load(self, filename):
        """
        Loads a pre-trained language model
        """
        with open(filename, 'rb') as f:
            dct = pickle.load(f)
            self.total_count = dct['total_count']
            self.word_count = defaultdict(int, dct['word_count'])
            self._update_log_quotient()

    def save(self, filename):
        """
        Saves the language model to a file
        """
        print('saving language model')
        with open(filename, 'wb') as f:
            pickle.dump(
                {'total_count':self.total_count,
                 'word_count':[ (w,c) for w,c in self.word_count.items()
                                if c >= self.threshold ]},
                f)


    @classmethod
    def train_from_dump(cls, filename):
        """
        Trains a bag of words language model from either a .txt
        file (in which case it is read as plain text) or a .json.bz2
        file (in which case it is read as a wikidata dump).
        """
        bow = BOWLanguageModel()
        if filename.endswith('.txt'):
            with open(filename, 'r') as f:
                for line in f:
                    bow.ingest_phrases([line.strip()])

        elif filename.endswith('.json.bz2'):
            with WikidataDumpReader(filename) as reader:
                for idx, item in enumerate(reader):
                    if idx % 10000 == 0:
                        print(idx)

                    enlabel = item.get('labels', {}).get('en', {}).get('value')
                    endesc = item.get('descriptions', {}).get('en', {}).get('value')
                    if enlabel:
                        # Fetch aliases
                        enaliases = [
                            alias['value']
                            for alias in item.get('aliases', {}).get('en', [])
                        ]

                        bow.ingest_phrases(enaliases + [enlabel])
        else:
            raise ValueError('invalid filename provided (must end in .txt or .json.bz2)')

        return bow


