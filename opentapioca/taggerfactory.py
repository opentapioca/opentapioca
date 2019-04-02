import json
import requests
from opentapioca.typematcher import TypeMatcher
from opentapioca.dumpreader import WikidataDumpReader

class CollectionAlreadyExists(Exception):
    pass

class TaggerFactory(object):
    """
    This helps creating and filling solr indices
    to be used by Tagger objects to detect mentions
    of entities in text.
    """

    def __init__(self,
                 solr_endpoint='http://localhost:8983/solr/',
                 type_matcher=None):
        """
        A type matcher can be provided to restrict the indexed
        items to particular classes.
        """
        self.solr_endpoint = solr_endpoint
        self.type_matcher = type_matcher or TypeMatcher()

    def create_collection(self, collection_name, num_shards=1):
        """
        Creates a collection and inits it with the
        appropriate index structure to be used by a tagger object.
        """
        r = requests.get(self.solr_endpoint + 'admin/collections', {
            'action':'CREATE',
            'name':collection_name,
            'collection.configName':'affiliations',
            'numShards':num_shards})
        if r.status_code == 400 and "already exists" in r.text:
            raise CollectionAlreadyExists('Collection "{}" already exists.'.format(collection_name))
        r.raise_for_status()

    def delete_collection(self, collection_name):
        """
        Drops a solr collection.
        """
        r = requests.get(self.solr_endpoint + 'admin/collections', {'action':'DELETE','name':collection_name})
        r.raise_for_status()

    def index_wd_dump(self,
          collection_name,
          dump_fname,
          profile,
          batch_size=5000,
          max_lines=100000000,
          commit_time=100):
        """
        Given a collection name and a path to a Wikidata .json.bz2 dump,
        index this wikidata dump in the solr collection.

        :param batch_size: the number of updates to send together to Solr
        :param max_lines: the maximum of items to read from the dump
        :param commit_time: commit the solr documents ever commit_time items.
        :param profile: the IndexingProfile to create the collection
        """
        batches_since_commit = 0
        with WikidataDumpReader(dump_fname) as reader:

            batch = []
            for idx, item in enumerate(reader):
                if idx > max_lines:
                    break
                
                doc = profile.entity_to_document(item, self.type_matcher)
                if doc is None:
                    continue

                batch.append(doc)

                if len(batch) >= batch_size:
                    print(idx)
                    print(doc)
                    batches_since_commit += 1
                    commit = False
                    if batches_since_commit >= commit_time:
                        commit = True
                        batches_since_commit = 0
                    self._push_documents(batch, collection_name, commit)
                    batch = []

            if batch or batches_since_commit:
                self._push_documents(batch, collection_name, True)

    def _push_documents(self, docs, collection, commit=False):
        r = requests.post('http://localhost:8983/solr/{collection}/update'.format(collection=collection),
            params={'commit': 'true' if commit else 'false'},
            data=json.dumps(docs), headers={'Content-Type':'application/json'})
        r.raise_for_status()
        print(r.json())



