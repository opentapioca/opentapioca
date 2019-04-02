import os
import pytest
import json
import requests_cache

from opentapioca.wditem import WikidataItemDocument

@pytest.fixture()
def cache_requests():
    testdir = os.path.dirname(os.path.abspath(__file__))
    location = os.path.join(testdir, 'data/requests_cache')
    requests_cache.install_cache(cache_name=location)
    yield
    requests_cache.uninstall_cache()
    
@pytest.fixture
def testdir():
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def load_item():
    def load(qid):
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', qid+'.json')
        with open(filename, 'r') as f:
            return WikidataItemDocument(json.load(f))
    return load
