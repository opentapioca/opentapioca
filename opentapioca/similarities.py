
"""
A collection of similarity measures between
items
"""

class EdgeSimilarityMeasure(object):
    def compute_similarity(self, a, b):
        """
        Computes the similarity between two tags.

        :param a: the starting item
        :param b: the target item
        """
        qid_a = int(a.id[1:])
        qid_b = int(b.id[1:])
        edges_a = set(a.edges)
        edges_b = set(b.edges)
        
        return self.similarity_from_edges(qid_a, qid_b, edges_a, edges_b)

    def similarity_from_edges(self, qid_a, qid_b, edges_a, edges_b):
        """
        This is the method that should be implemented by subclasses.
        """
        raise NotImplemented

class DirectLinkSimilarity(EdgeSimilarityMeasure):
    """
    We just replicate Wikidata's edges - weighing is done
    downstream.
    """
    def similarity_from_edges(self, qid_a, qid_b, edges_a, edges_b):
        score = 0.
        if qid_a == qid_b or qid_b in edges_a:
            score += 1.
        if qid_b == qid_a or qid_a in edges_b:
            score += 1.
        return score

class EdgeRatioSimilarity(EdgeSimilarityMeasure):
    def similarity_from_edges(self, qid_a, qid_b, edges_a, edges_b):
        # Add self link
        edges_a.add(qid_a)
        edges_b.add(qid_b)

        len_common = float(len(edges_a.intersection(edges_b)))

        return 0.5* ( len_common  / len(edges_a) + len_common / len(edges_b))


class OneStepSimilarity(EdgeSimilarityMeasure):
    def __init__(self, beta):
        self.beta = beta

    def similarity_from_edges(self, qid_a, qid_b, edges_a, edges_b):
        beta = self.beta
        len_common = float(len(edges_a.intersection(edges_b)))
        proba = 0.
        if qid_a == qid_b:
            proba += beta * beta
        if qid_b in edges_a:
            proba += (1- beta)*beta/len(edges_a)
        if qid_a in edges_b:
            proba += beta*(1-beta)/len(edges_b)
        if len_common:
            proba += (1-beta)*(1-beta)*(len_common/len(edges_a))*(len_common/len(edges_b))

        return proba
