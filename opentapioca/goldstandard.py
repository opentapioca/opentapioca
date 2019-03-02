import json
import pynif
import urllib

class GoldStandardDataset(object):
    """
    A dataset which stores all possible annotations on each document
    (all items with matching labels).
    """
    def __init__(self, fname):
        self.fname = fname
        self.load()

    def load(self):
        self.doi_docs = []
        self.judgments = {}
        with open(self.fname, 'r') as f:
            for line in f:
                fields = line.strip().split('\t')
                doi = fields[0]
                doc = fields[1]
                self.doi_docs.append((doi, doc))
                if len(fields) >= 3:
                    judgment = json.loads(fields[2])
                    self.judgments[(doi,doc)] = judgment

    def save(self):
        with open(self.fname, 'w') as f:
            for doi, doc in self.doi_docs:
                fields = [doi, doc]
                if (doi, doc) in self.judgments:
                    fields.append(json.dumps(self.judgments[(doi,doc)]))
                f.write('\t'.join(fields)+'\n')

    def get_unannotated_doi_doc(self):
        for doi, doc in self.doi_docs:
            if (doi,doc) not in self.judgments:
                return (doi,doc)

    def set_judgments(self, doi, doc, judgment):
        self.judgments[(doi,doc)] = judgment

    def get_item_choices(self, doi_doc):
        """
        Returns the item chosen for each mention
        in a given document
        """
        judgment = self.judgments[doi_doc]
        mention_ids = set()
        item_choices = {}

        for decision in judgment:
            mention_id = (decision['start'],decision['end'])
            mention_ids.add(mention_id)
            if decision['valid']:
                item_choices[mention_id] = decision['qid']

        for mention_id in mention_ids:
            if not mention_id in item_choices:
                item_choices[mention_id] = None
        return item_choices


    def to_nif(self, corpus_uri):
        """
        Returns a NIF representation of this dataset
        """
        collection = pynif.NIFCollection(uri=corpus_uri)
        for idx, (doi,doc) in enumerate(self.doi_docs):
            context = collection.add_context(
                mention=doc,
                uri=corpus_uri + '/{}'.format(idx))
            context.sourceUrl='https://doi.org/' +urllib.parse.quote(doi)
            item_choices = self.get_item_choices((doi,doc))
            for (start,end) in item_choices:
                qid = item_choices[(start,end)]
                if qid is None:
                    continue
                identRef = 'http://www.wikidata.org/entity/'+ qid
                phrase = context.add_phrase(beginIndex=start,
                    endIndex=end,
                    taIdentRef=identRef)
        return collection
