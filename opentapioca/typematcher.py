from .utils import to_q
from .sparqlwikidata import sparql_wikidata

class TypeMatcher(object):
    """
    Interface that caches the subclasses of parent classes.
    Cached in memory.
    """

    def __init__(self, subclass_pid='P279'):
        self.subclass_pid = subclass_pid
        self.sets = {}

    def is_subclass(self, qid_1, qid_2):
        """
        Checks if the Wikidata item designated by
        the first QID is a subclass of the second.

        Equivalent SPARQL query:
        ?qid_1 wdt:P279* ?qid_2

        This is done by caching the children of
        the class via the "subclass of" (P279)
        relation.
        """
        if not qid_2 in self.sets:
            self.prefetch_children(qid_2)
        return int(qid_1[1:]) in self.sets[qid_2]

    def prefetch_children(self, qid, force=False):
        """
        Prefetches (in Redis) all the children of a given class
        """

        if qid in self.sets:
            return # children are already prefetched

        sparql_query = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        SELECT ?child WHERE { ?child wdt:%s* wd:%s }
        """ % (self.subclass_pid, qid)
        results = sparql_wikidata(sparql_query)

        new_set = set()
        for result in results["bindings"]:
            child_qid = to_q(result["child"]["value"])
            new_set.add(int(child_qid[1:]))

        self.sets[qid] = new_set


