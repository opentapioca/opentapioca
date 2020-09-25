import json
import re
import logging

from .apireaderbase import APIReaderBase
from opentapioca.sparqlwikidata import sparql_wikidata
from opentapioca.utils import to_q

logger = logging.getLogger(__name__)

class SparqlReader(APIReaderBase):
    """
    Generates a collection of `WikidataItemDocument` from
    a SPARQL query which contains an "item" variable.
    """

    def __init__(self,
                 query,
                 endpoint='https://query.wikidata.org/sparql',
                 mediawiki_api='https://www.wikidata.org/w/api.php'):
        super(SparqlReader, self).__init__(mediawiki_api)
        self.endpoint = endpoint
        self.query = query
        self.batch_size = 50
        self.query_results = None

    def __enter__(self):
        self.query_results = sparql_wikidata(self.query, endpoint=self.endpoint)['bindings']
        return self

    def __exit__(self, *args, **kwargs):
        return None

    def __iter__(self):
        if self.query_results is None:
            raise ValueError('Query results have not been fetched.')
        while self.query_results:
            batch = self.query_results[:self.batch_size]
            self.query_results = self.query_results[self.batch_size:]

            qids = [to_q(result['item']['value']) for result in batch if 'item' in result]
            qids_without_none = [qid for qid in qids if qid]

            # Fetch item contents
            for item in self.fetch_items(qids_without_none):
                yield item

