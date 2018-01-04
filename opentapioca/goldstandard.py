import json

class GoldStandardDataset(object):
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


