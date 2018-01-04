import sys
import requests
import json
from .typematcher import TypeMatcher
from .languagemodel import BOWLanguageModel
from .dumpreader import WikidataDumpReader

def push_documents(docs, collection, commit=False):
    r = requests.post('http://localhost:8983/solr/{collection}/update'.format(collection=collection),
        params={'commit': 'true' if commit else 'false'},
        data=json.dumps(docs), headers={'Content-Type':'application/json'})
    r.raise_for_status()
    print(r.json())

type_matcher = TypeMatcher()
bow = BOWLanguageModel()
bow_fname = 'bow.pkl'


def mkdocs(fname, collection,
          batch_size=5000,
          max_lines=100000000,
          commit_time=100,
          restrict_type=None,
          aliases=True):
    """
    Reads a Wikidata dump and produces Solr documents for ingestion
    by the search index.
    """

    batches_since_commit = 0
    with WikidataDumpReader(fname) as reader:

        batch = []
        for idx, item in enumerate(reader):
            if idx > max_lines:
                break

            valid_type_qids = item.get_types()

            if restrict_type:
                correct_type = any([
                            any([
                                type_matcher.is_subclass(qid, type_qid)
                                for type_qid in restrict_type
                            ])
                            for qid in valid_type_qids ])
                if not correct_type:
                    continue

            enlabel = item.get_default_label()
            endesc = item.get('descriptions', {}).get('en', {}).get('value')
            if enlabel:
                # Fetch aliases
                aliases = item.get_all_terms()
                aliases.remove(enlabel)
                # Edges
                edges = item.get_outgoing_edges(include_p31=False, numeric=True)
                valid_grids = item.get_identifiers('P2427')

                # Stats
                nb_statements = item.get_nb_statements()
                nb_sitelinks = item.get_nb_sitelinks()

                # numeric types
                numeric_types = [ int(q[1:]) for q in valid_type_qids ]

                doc = {'id': item.get('id'),
                       'label': enlabel,
                       'desc': endesc or '',
                       'type': numeric_types,
                       'edges': edges,
                       'grid': ','.join(valid_grids),
                       'aliases': list(aliases),
                       'nb_statements': nb_statements,
                       'nb_sitelinks': nb_sitelinks}
                batch.append(doc)

            if len(batch) >= batch_size:
                print(idx)
                print(doc)
                batches_since_commit += 1
                commit = False
                if batches_since_commit >= commit_time:
                    commit = True
                    batches_since_commit = 0
                push_documents(batch, collection, commit)
                batch = []

        if batch:
            push_documents(batch, collection, True)


if __name__ == '__main__':
    restrict_type = None
    if len(sys.argv) >= 4:
        restrict_type = sys.argv[3].split(',')
        print(restrict_type)
    mkdocs(sys.argv[1], sys.argv[2], restrict_type=restrict_type)
