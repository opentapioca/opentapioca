
import pytest
import requests_mock
import os

from opentapioca.readers.sparqlreader import SparqlReader
from .test_fixtures import wbgetentities_response
from .test_fixtures import testdir

@pytest.fixture
def dummy_sparql_query_response(testdir):
    with open(os.path.join(testdir, 'data', 'dummy_sparql_query_response.json'), 'r') as f:
        return f.read()

def test_iterate(wbgetentities_response, dummy_sparql_query_response):
    query = "mysparqlquery"
    reader = SparqlReader(query)
    with requests_mock.mock() as mocker:
        mocker.get('https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=Q123%7CQ456%7CQ789', text=wbgetentities_response)
        mocker.get('https://query.wikidata.org/sparql?format=json&query=mysparqlquery', text=dummy_sparql_query_response)

        with reader as entered_reader:
            items = list(entered_reader)

            assert [item.get('id') for item in items] == ['Q123', 'Q456']
