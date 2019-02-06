import os
import pytest
import requests_cache

@pytest.fixture()
def cache_requests():
    testdir = os.path.dirname(os.path.abspath(__file__))
    location = os.path.join(testdir, 'data/requests_cache')
    requests_cache.install_cache(cache_name=location)
    yield
    requests_cache.uninstall_cache()