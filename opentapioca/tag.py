import json

class Tag(object):
    """
    A tag is a candidate annotation for a mention.
    """

    def __init__(self, id=None,
                 label=None, aliases=None, desc=None,
                 extra_aliases=None,
                 nb_statements=None, nb_sitelinks=None,
                 edges=None, types=None,
                 rank=None, similarities=None,
                 score=None, valid=None):
        """
        :param id: the Wikidata Qid of the linked entity
        :param label: the label of the entity in our preferred language
        :param aliases: the aliases of the entity in our preferred language
        :param extra_aliases: extra aliases deduced from claim values
        :param desc: the description of the entity in our preferred language (only used for display purposes)
        :param nb_statements: number of statements on the item (used as a popularity measure)
        :param nb_sitelinks: number of sitelinks (links to Wikimedia projects), used as a popularity measure
        :param edges: links to other entities, represented as a list of integers
        :param rank: PageRank of this entity
        :param similarities: map containing the similarity of this item with other neighboring tags
        :param score: score of the tag as computed by the classifier
        :param types: json representation of type matches
        :param valid: is this tag known to be true for this mention? None if unknown
        """
        self.id = id
        self.label = label
        self.aliases = aliases
        self.extra_aliases = extra_aliases
        self.desc = desc
        self.nb_statements = nb_statements
        if isinstance(nb_statements, list):
            self.nb_statements = nb_statements[0]
        self.nb_sitelinks = nb_sitelinks
        if isinstance(nb_sitelinks, list):
            self.nb_sitelinks = nb_sitelinks[0]
        self.edges = edges
        self.types = json.loads(types)
        self.rank = rank
        self.similarities = similarities
        self.score = score
        self.valid = valid

    def json(self):
        return {
            'id': self.id,
            'label': self.label,
            'aliases': self.aliases,
            'extra_aliases': self.extra_aliases,
            'desc': self.desc,
            'nb_statements': self.nb_statements,
            'nb_sitelinks': self.nb_sitelinks,
            'edges': self.edges,
            'types': self.types,
            'rank': self.rank,
            'score': self.score,
            'valid': self.valid,
        }

    def __repr__(self):
        return '<Tag: {}>'.format(self.id)
