import os
import unittest
import requests_mock
import re
from opentapioca.typematcher import TypeMatcher
from .test_fixtures import cache_requests

def test_typematcher(cache_requests):
    t = TypeMatcher()
    # First query (cached by cache_requests
    # any university (Q3918) is an organization (Q43229)
    assert t.is_subclass('Q3918', 'Q43229')
    
    # Second query disabled - still works because of local caching
    with requests_mock.Mocker(real_http=True) as mocker:
        mocker.get(re.compile('.*'), status_code=500)
        assert t.is_subclass('Q3918', 'Q43229')