import json
import requests
from math import log

from .languagemodel import BOWLanguageModel
from .wikidatagraph import WikidataGraph
from .similarities import EdgeRatioSimilarity
from .similarities import OneStepSimilarity
from .similarities import DirectLinkSimilarity

solr_collection = 'wd_multilingual'

class Tagger(object):
    """
    The tagger indexes a Wikidata dump in Solr
    and uses it to detect efficiently mentions of Wikidata
    items in text.
    """
    
    def __init__(self, bow, graph):
        self.bow = bow
        self.graph = graph
        self.solr_endpoint = 'http://localhost:8983/solr/{}/tag'.format(solr_collection)
        self.coef = 5
        self.similarity_method = DirectLinkSimilarity()

    def dictify(self, lst):
        """
        Converts a list of [key1,val1,key2,val2,...] to a dict
        """
        return {
            lst[2*k]: lst[2*k+1]
            for k in range(len(lst)//2)
        }

    def tag_and_rank(self, phrase, prune=True):
        # Tag
        r = requests.post(self.solr_endpoint,
            params={'overlaps':'NO_SUB',
             'tagsLimit':5000,
             'fl':'id,label,aliases,desc,grid,nb_statements,nb_sitelinks,edges,type',
             'wt':'json',
             'indent':'on',
            },
            headers ={'Content-Type':'text/plain'},
            data=phrase.encode('utf-8'))
        resp = r.json()

        # Enhance mentions with page rank and edge similarity
        mentions = [
            self.dictify(mention)
            for mention in resp.get('tags', [])
        ]
        docs = {
            doc['id']:doc
            for doc in resp.get('response', {}).get('docs', [])
        }

        ranked_mentions = [
            self.enhance_mention(phrase, mention, docs, mentions)
            for mention in mentions
        ]

        if prune:
            ranked_mentions = list(filter(self.prune_mention, ranked_mentions))

        return ranked_mentions

    def tag_id(self, qid, start, end):
        return "%d-%d-%s" % (start, end, qid)

    def prune_mention(self, mention):
        phrase = mention['phrase']
        # filter out small uncapitalized words
        if len(phrase) <= 2 and phrase.lower() == phrase:
            return False

        return True

    def enhance_mention(self, phrase, mention, docs, mentions):
        """
        :param phrase: the original document
        :param mention: the mention to enhance with scores
        :param docs: dictionary from qid to item
        :param mentions: the list of all mentions in the document
        :returns: the enhanced mention, as a dictionary
        """
        start = mention['startOffset']
        end = mention['endOffset']
        surface = phrase[start:end]
        surface_score = self.bow.log_likelihood(surface)
        ranked_qids = []
        for qid in mention['ids']:
            item = dict(docs[qid].items())

            # Compute similarity to other items in the same document
            similarities = []
            other_tag_ids = []
            for other_mention in mentions:
                other_start = other_mention['startOffset']
                other_end = other_mention['endOffset']
                if other_start == start and other_end == end:
                    continue
                for other_qid in other_mention['ids']:
                    other_tag_id = (other_start, other_end, other_qid)
                    other_item = docs[other_qid]
                    similarity = self.similarity_method.compute_similarity(item, other_item)
                    other_tag_ids.append(other_tag_id)
                    if similarity > 0.:
                        similarities.append(
                                {'tag': other_tag_id,
                                 'score': similarity })

            # Normalize
            weight_sum = sum(similarity['score'] for similarity in similarities)
            if weight_sum == 0.:
                # the item is not similar to anything else
                # we add dummy edges to all other tags, so that the probability
                # mass is retained
                similarities.append({
                    'tag':(start,end,qid),
                    'score':1.})
                for tag in other_tag_ids:
                    similarities.append({
                        'tag':tag,
                        'score':1.})
                weight_sum = len(other_tag_ids)+1

            similarities = [
                    {'tag':sim['tag'],'score': sim['score']/weight_sum}
                    for sim in similarities
            ]

            item.update({
                'rank': 25. + log(self.graph.get_pagerank(qid)),
                'similarities': similarities,
            })
            ranked_qids.append(item)
        return {
            'phrase': surface,
            'start': start,
            'end': end,
            'log_likelihood': -surface_score,
            'tags': sorted(ranked_qids, key=lambda tag: -tag['rank'])[:10],
        }


if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    print('Loading '+fname)
    bow = BOWLanguageModel()
    bow.load(fname)
    print('Loading '+sys.argv[2])
    graph = WikidataGraph()
    graph.load_pagerank(sys.argv[2])
    tagger = Tagger(bow, graph)

    while True:
        phrase = input('>>> ')
        tags = tagger.tag_and_rank(phrase)
        for mention in tags:
            for tag in mention.get('tags', []):
                if 'edges' in tag:
                    del tag['edges']
                if 'aliases' in tag:
                    del tag['aliases']
        print(json.dumps(tags, indent=2, sort_keys=True))

