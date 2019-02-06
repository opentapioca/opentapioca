import re

q_re = re.compile(r'(<?https?://www.wikidata.org/(entity|wiki)/)?(Q[0-9]+)>?')
p_re = re.compile(r'(<?https?://www.wikidata.org/(entity/|wiki/Property:))?(P[0-9]+)>?')

def to_q(url):
    """
    Normalizes a Wikidata item identifier

    >>> to_q('Q1234')
    'Q1234'
    >>> to_q('<http://www.wikidata.org/entity/Q801> ')
    'Q801'
    """
    if type(url) != str:
        return
    match = q_re.match(url.strip())
    if match:
        return match.group(3)

def to_p(url):
    """
    Normalizes a Wikidata property identifier

    >>> to_p('P1234')
    'P1234'
    >>> to_p('<http://www.wikidata.org/entity/P801> ')
    'P801'
    """
    if type(url) != str:
        return
    match = p_re.match(url.strip())
    if match:
        return match.group(3)


