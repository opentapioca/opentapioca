
import os
import pytest
import json

from opentapioca.typematcher import TypeMatcher
from opentapioca.indexingprofile import TypeConstraint
from opentapioca.indexingprofile import IndexingProfile
from opentapioca.readers.dumpreader import WikidataDumpReader
from .test_fixtures import testdir
from .test_fixtures import load_item

# # Stubs and fixtures


class TypeMatcherStub(TypeMatcher):

    def __init__(self):
        super(TypeMatcherStub, self).__init__()
        self.sets['Q5'] = {5}
        self.sets['Q43229'] = {43229, 3918, 43702}
        self.sets['Q618123'] = {618123, 43702}

    def prefetch_children(self):
        raise ValueError('SPARQL queries disabled, use self.sets[parent_qid] = {child_qids}')


@pytest.fixture
def sample_profile(testdir):
    return IndexingProfile.load(os.path.join(testdir, 'data', 'indexing_profile.json'))


@pytest.fixture
def expected_json():
    return {
        'language': 'en',
        'name': 'affiliations',
        'restrict_properties': ['P2427', 'P1566', 'P496'],
        'restrict_types': [
            {'type': 'Q43229', 'property': 'P31'},
            {'type': 'Q618123', 'property': 'P31'},
            {'type': 'Q5', 'property': 'P31'},
        ],
        'alias_properties': [
            {'property': 'P496', 'prefix': None},
            {'property': 'P2002', 'prefix': '@'},
            {'property': 'P4550', 'prefix': None},
        ]
    }

# # Tests


def test_type_constraint(load_item):
    item = load_item('Q62653454')
    constraint = TypeConstraint(pid='P31', qid='Q5')
    assert constraint.satisfied(item, TypeMatcherStub())


def test_load_indexing_profile(testdir, expected_json):
    indexing_profile = IndexingProfile.load(os.path.join(testdir, 'data', 'indexing_profile.json'))

    assert indexing_profile.language == 'en'
    assert indexing_profile.name == 'affiliations'
    assert indexing_profile.restrict_properties == ['P2427', 'P1566', 'P496']
    assert indexing_profile.json() == expected_json


def test_save_indexing_profile(testdir, sample_profile, expected_json):
    filename = os.path.join(testdir, 'data', 'written_indexing_profile.json')
    try:
        sample_profile.save(filename)
        with open(filename, 'r') as f:
            assert json.load(f) == expected_json
    finally:
        os.remove(filename)

def test_entity_to_document(sample_profile, load_item):
    item = load_item('Q62653454')
    doc = sample_profile.entity_to_document(item, TypeMatcherStub())
    assert doc is not None
    assert doc['label'] == 'Elisabeth Hauterive'
    assert doc['revid'] == 900557325


def test_multiple_types(sample_profile, load_item):
    item = load_item('Q31')
    doc = sample_profile.entity_to_document(item, TypeMatcherStub())
    assert doc is not None
    assert doc['extra_aliases'] == []
    types = json.loads(doc['types'])
    assert types['Q618123']
    assert types['Q43229']

def test_filtered_out_entity(sample_profile, load_item):
    item = load_item('Q8502')
    doc = sample_profile.entity_to_document(item, TypeMatcherStub())
    assert doc is None

def test_extra_aliases(sample_profile, load_item):
    item = load_item('Q51783269')
    doc = sample_profile.entity_to_document(item, TypeMatcherStub())
    assert doc is not None
    types = json.loads(doc['types'])
    assert types['P2427']
    assert set(doc['extra_aliases']) == {'@IRIF_Paris', 'UMR8243'}

def test_all_items_profile(testdir):
    profile_filename = os.path.join(testdir, 'data/all_items_profile.json')
    profile = IndexingProfile.load(profile_filename)
    type_matcher = TypeMatcherStub()
    dump_filename = os.path.join(testdir, 'data/sample_wikidata_items.json.bz2')
    with WikidataDumpReader(dump_filename) as reader:
        for item in reader:
            assert profile.entity_to_document(item, type_matcher) is not None

