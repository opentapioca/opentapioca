import json
import re
import logging

from sseclient import SSEClient
from .apireaderbase import APIReaderBase

logger = logging.getLogger(__name__)

class WikidataStreamReader(APIReaderBase):
    """
    Generates a stream of `WikidataItemDocument` from
    the Wikidata edit stream.
    """

    def __init__(self,
                 endpoint='https://stream.wikimedia.org/v2/stream/recentchange',
                 wiki='wikidatawiki',
                 mediawiki_api='https://www.wikidata.org/w/api.php',
                 from_time=None):
        super(WikidataStreamReader, self).__init__(mediawiki_api)
        self.endpoint = endpoint
        self.wiki = wiki
        self.from_time = from_time
        self.stream = None
        self.item_buffer = []
        self.batch_size = 50
        self.namespaces = [0]
        self.id_re = re.compile(r'^Q[1-9]\d+$')

    def __enter__(self):
        url = self.endpoint
        if self.from_time is not None:
             url += '?since='+self.from_time.isoformat().replace('+00:00', 'Z')
        self.stream = SSEClient(url)
        return self

    def __exit__(self, *args, **kwargs):
        return None

    def __iter__(self):
        if not self.stream:
            raise ValueError('Stream has not been started.')
        stream_ended = False
        while not stream_ended:
            # Fetch new batch of events
            qids = [self.fetch_next_qid() for _ in range(self.batch_size)]

            stream_ended = None in qids
            qids_without_none = {qid for qid in qids if qid}

            # Fetch item contents
            for item in self.fetch_items(qids_without_none):
                yield item

    def fetch_next_qid(self):
        """
        Fetches the next Qid in the Wikidata edit stream
        """
        for event in self.stream:
            if event.event == 'message':
                try:
                    change = json.loads(event.data)
                    if (change.get('wiki') == self.wiki and
                        change.get('namespace') in self.namespaces and
                        change.get('title') and
                        self.id_re.match(change['title'])):
                        return change['title']
                except ValueError:
                    pass


