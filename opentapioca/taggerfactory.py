import json
import requests
import logging
from opentapioca.typematcher import TypeMatcher

logger = logging.getLogger(__name__)

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

    def create_collection(self, collection_name, num_shards=1, configset='tapioca'):
        """
        Creates a collection and inits it with the
        appropriate index structure to be used by a tagger object.
        """
        r = requests.get(self.solr_endpoint + 'admin/collections', {
            'action':'CREATE',
            'name':collection_name,
            'collection.configName':configset,
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

    def index_stream(self,
          collection_name,
          stream,
          profile,
          batch_size=5000,
          max_lines=None,
          commit_time=10,
          delete_excluded=False,
          skip_docs=0):
        """
        Given a stream of Wikidata items, index it in the given solr collection.

        :param profile: the IndexingProfile to create the collection
        :param batch_size: the number of updates to send together to Solr
        :param max_lines: the maximum of items to read from the dump
        :param commit_time: commit the solr documents ever commit_time items.
        :param delete_excluded: delete excluded entities from the Solr index.
        """
        batches_since_commit = 0
        with stream as reader:

            batch = {}
            for idx, item in enumerate(reader):
                if max_lines is not None and idx > max_lines:
                    break
                if skip_docs > 0 and idx < skip_docs:
                    continue

                doc = profile.entity_to_document(item, self.type_matcher)
                qid = item.get('id')

                if doc is None and not delete_excluded:
                    continue

                batch[qid] = doc
                if len(batch) >= batch_size:
                    logger.info('Stream index: {}'.format(idx))
                    batches_since_commit += 1
                    commit = False
                    if batches_since_commit >= commit_time:
                        commit = True
                        batches_since_commit = 0
                    self._push_documents(batch, collection_name, commit)
                    batch = {}

            if batch or batches_since_commit:
                self._push_documents(batch, collection_name, True)

    def _collection_update_endpoint(self, collection):
        """
        Returns the URL where updates are pushed.
        """
        return '{endpoint}{collection}/update'.format(endpoint=self.solr_endpoint, collection=collection)

    def _push_documents(self, docs, collection, commit=False):
        """
        Sends documents to Solr for indexing.
        If configured correctly, Solr will deal with the versioning on its
        own, so we do not need to check that we are pushing outdated results.

        :param docs: map from ids to documents. None values will be interpreted as deletions.
        """
        docs_to_add = [doc for doc in docs.values() if doc is not None]
        ids_to_delete = [id for id, doc in docs.items() if doc is None]
        logger.info('Updating {} docs, deleting {} others'.format(len(docs_to_add), len(ids_to_delete)))
        payload = {
            'add': docs_to_add,
            'delete': ids_to_delete,
        }
        r = requests.post(self._collection_update_endpoint(collection),
            params={'commit': 'true' if commit else 'false'},
            data=json.dumps(payload), headers={'Content-Type':'application/json'})
        r.raise_for_status()



