import logging
import requests

from time import sleep
from opentapioca.wditem import WikidataItemDocument

logger = logging.getLogger(__name__)

class APIReaderBase(object):
    """
    Base class for a reader that relies on the MediaWiki API to fetch
    item contents.
    """

    def __init__(self, mediawiki_api):
        self.mediawiki_api = mediawiki_api
        self.retries = 5
        self.delay = 5

    def fetch_items(self, qids):
        """
        Given a list of qids, fetch the corresponding documents via the Wikidata API.
        """
        if not qids:
            return []
        for retries in range(self.retries):
            try:
                req = requests.get(self.mediawiki_api, {
                    'format':'json',
                    'action':'wbgetentities',
                    'ids':'|'.join(qids)})
                req.raise_for_status()
                result = req.json().get('entities').values()
                return [WikidataItemDocument(payload) for payload in result if 'missing' not in payload]
            except (requests.exceptions.RequestException, ValueError, TypeError, AttributeError) as e:
                logger.warning(e)
                if retries < self.retries-1:
                    sleep_time = (1+retries)*self.delay
                    logger.info('Retrying wbgetentities in {}'.format(sleep_time))
                    sleep(sleep_time)
                else:
                    logger.error('Failed to fetch entities')
                    logger.error(req.url)
                    raise


