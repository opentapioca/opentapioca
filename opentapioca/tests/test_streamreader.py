import os
import pytest
import requests.exceptions
import requests_mock
import json

from pytest_mock import mocker
from opentapioca.readers.streamreader import WikidataStreamReader
from collections import namedtuple
from .test_fixtures import testdir
from opentapioca.wditem import WikidataItemDocument

EventStubBase = namedtuple('EventStubBase', ['data', 'event'])


def EventStub(event='message', wiki='wikidatawiki', namespace=0, title='Q123'):
    return EventStubBase(event=event, data=json.dumps(
            {'wiki':wiki, 'namespace':namespace, 'title':title}
            ))


@pytest.fixture
def wbgetentities_response(testdir):
    with open(os.path.join(testdir, 'data', 'wbgetentities_response.json'), 'r') as f:
        return f.read()


@pytest.fixture
def event_stream():
    return [
        EventStub(event='something happened'),
        EventStub(title='Q123'),
        EventStub(title='NewItem'),
        EventStub(namespace=2),
        EventStub(title='Q456'),
        EventStub(title='Q789'),
        EventStub(wiki='enwiki'),
    ]


def test_fetch_items(wbgetentities_response):
    reader = WikidataStreamReader()
    with requests_mock.mock() as mocker:
        mocker.get('https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=Q123%7CQ456%7CQ789', text=wbgetentities_response)

        items = reader.fetch_items(['Q123', 'Q456', 'Q789'])

        assert len(items) == 2  # Q789 does not exist
        assert items[0].get_types() == ['Q47018901']


def test_fetch_items_500_error(wbgetentities_response):
    reader = WikidataStreamReader()
    reader.delay = 0
    with requests_mock.mock() as mocker:
        mocker.get('https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=Q123%7CQ456%7CQ789', status_code=500)

        with pytest.raises(requests.exceptions.RequestException):
            items = reader.fetch_items(['Q123', 'Q456', 'Q789'])


class StreamReaderStub(WikidataStreamReader):

    def __init__(self, events):
        super(StreamReaderStub, self).__init__()
        self.stub_events = events

    def __enter__(self):

        def generate():
            for event in self.stub_events:
                yield event

        self.stream = generate()
        return self


def test_iterate(event_stream, wbgetentities_response, mocker):
    reader = StreamReaderStub(event_stream)
    method = mocker.patch.object(reader, 'fetch_items')
    method.return_value = [WikidataItemDocument({'id':'Q123'}), WikidataItemDocument({'id':'Q456'})]

    with reader as entered_reader:
        items = list(entered_reader)

        method.assert_called_with({'Q123', 'Q456', 'Q789'})
        method.assert_called_once()
        assert [item.get('id') for item in items] == ['Q123', 'Q456']



