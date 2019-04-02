import unittest
import os
import json
from opentapioca.wditem import WikidataItemDocument
from .test_fixtures import load_item

def test_parse_item(load_item):
    item = load_item('Q30264236')
    assert item.get_nb_statements() == 9
    assert item.get_nb_sitelinks() == 0
    assert item.get_types() == ['Q31855']
    assert set(item.get_outgoing_edges()) == {31855, 148, 530471, 9384257, 185684}
    assert str(item) == '<WikidataItemDocument Q30264236>'
    
def test_language_fallback(load_item):
    """
    If there is no label in the preferred language (en),
    we fallback on any other language.
    """
    item = load_item('Q62653454')
    assert item.get_default_label('en') == 'Elisabeth Hauterive'
    assert item.get_default_label('fr') == 'Elisabeth Hauterive'
    