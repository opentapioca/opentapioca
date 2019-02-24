from pydoc import describe

class Tag(object):
    """
    A tag is a candidate annotation for a mention.
    """
    
    def __init__(self, id=None,
                 label=None, aliases=None, desc=None,
                 nb_statements=None, nb_sitelinks=None,
                 edges=None, type=None, grid=None,
                 rank=None, similarities=None):
        self.id = id
        self.label = label
        self.aliases = aliases
        self.desc = desc
        self.nb_statements = nb_statements
        self.edges = edges
        self.type = type
        self.grid = grid
        self.rank = rank
        self.similarities = similarities
        
    def json(self):
        return {
            'id': self.id,
            'label': self.label,
            'aliases': self.aliases,
            'desc': self.desc,
            'nb_statements': self.nb_statements,
            'nb_sitelinks': self.nb_sitelinks,
            'edges': self.edges,
            'type': self.type,
            'grid': self.grid,
            'rank': self.rank,
            'similarities': self.similarities,
        }
        
    def __repr__(self):
        return '<Tag: {}>'.format(self.id)