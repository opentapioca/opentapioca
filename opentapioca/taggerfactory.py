import json
import requests
from opentapioca.typematcher import TypeMatcher
from opentapioca.dumpreader import WikidataDumpReader

class TaggerFactory(object):
    """
    This helps creating and filling solr indices
    to be used by Tagger objects to detect mentions
    of entities in text.
    """
    
    def __init__(self,
                 solr_endpoint='http://localhost:8983/solr/',
                 type_matcher=None):
        """
        A type matcher can be provided to restrict the indexed
        items to particular classes.
        """
        self.solr_endpoint = solr_endpoint
        self.type_matcher = type_matcher or TypeMatcher()
    
    def create_collection(self, collection_name, num_shards=1):
        """
        Creates a collection and inits it with the 
        appropriate index structure to be used by a tagger object.
        """
        r = requests.get(self.solr_endpoint + 'admin/collections', {
            'action':'CREATE',
            'name':collection_name,
            'collection.configName':'affiliations',
            'numShards':num_shards})
        r.raise_for_status()
        tag_type="""
                  "add-field-type":{
            "name":"tag",
            "class":"solr.TextField",
            "postingsFormat":"Memory",
            "omitNorms":true,
            "multiValued":true,
            "indexAnalyzer":{
              "tokenizer":{ 
                 "class":"solr.StandardTokenizerFactory" },
              "filters":[
                {"class":"solr.EnglishPossessiveFilterFactory"},
                {"class":"solr.ASCIIFoldingFilterFactory"},
                {"class":"solr.LowerCaseFilterFactory"},
                {"class":"solr.ConcatenateGraphFilterFactory"}
              ]},
            "queryAnalyzer":{
              "tokenizer":{ 
                 "class":"solr.StandardTokenizerFactory" },
              "filters":[
                {"class":"solr.EnglishPossessiveFilterFactory"},
                {"class":"solr.ASCIIFoldingFilterFactory"},
                {"class":"solr.LowerCaseFilterFactory"}
              ]}
            },
        """
        # not stored as a dict because of the duplicate keys
        index_json = """{
          "add-field":{ "name":"label", "type":"text_general"},   
          "add-field":{ "name":"aliases", "type":"text_general", "multiValued":true },   
          "add-field":{ "name":"desc", "type":"text_general", "indexed":false },
          "add-field":{ "name":"grid", "type":"text_general", "indexed":false }, 
          "add-field":{ "name":"name_tag", "type":"tag", "stored":false, "multiValued":true },    
          "add-copy-field":{ "source":"label", "dest":[ "name_tag" ]},
          "add-copy-field":{ "source":"aliases", "dest":[ "name_tag" ]}
        }"""
        #r = requests.post(self.solr_endpoint + '{}/schema'.format(collection_name), index_json, headers={'Content-Type':'application/json'})
        #resp = r.json()
        #if resp.get('errors'):
        #    raise RuntimeError('Creating the index failed:\n\n'+'\n\n'.join(['\n'.join(err.get('errorMessages')) or '' for err in resp.get('errors')]))
        #r.raise_for_status()
        
        tagger_config = {
          "add-requesthandler" : {
            "name": "/tag",
            "class":"org.opensextant.solrtexttagger.TaggerRequestHandler",
            "defaults":{ "field":"name_tag" }
          }
        }
        #r = requests.post(self.solr_endpoint + '{}/config'.format(collection_name), json.dumps(tagger_config))
        #r.raise_for_status()
        
    def delete_collection(self, collection_name):
        """
        Drops a solr collection.
        """
        r = requests.get(self.solr_endpoint + 'admin/collections', {'action':'DELETE','name':collection_name})
        r.raise_for_status()
        
    def index_wd_dump(self,
          collection_name,
          dump_fname,
          batch_size=5000,
          max_lines=100000000,
          commit_time=100,
          restrict_type=None,
          aliases=True):
        """
        Given a collection name and a path to a Wikidata .json.bz2 dump,
        index this wikidata dump in the solr collection.
        
        :param batch_size:
        :param max_lines: the maximum of items to read from the dump
        :param commit_time: commit the solr documents ever commit_time items.
        :param restrict_type: restrict the index to items of the any of the given types
        :param aliases: index aliases
        """
        batches_since_commit = 0
        with WikidataDumpReader(dump_fname) as reader:
    
            batch = []
            for idx, item in enumerate(reader):
                if idx > max_lines:
                    break
    
                valid_type_qids = item.get_types()
    
                if restrict_type:
                    correct_type = any([
                                any([
                                    self.type_matcher.is_subclass(qid, type_qid)
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
                    self._push_documents(batch, collection_name, commit)
                    batch = []
    
            if batch:
                self._push_documents(batch, collection_name, True)
                
    def _push_documents(self, docs, collection, commit=False):
        r = requests.post('http://localhost:8983/solr/{collection}/update'.format(collection=collection),
            params={'commit': 'true' if commit else 'false'},
            data=json.dumps(docs), headers={'Content-Type':'application/json'})
        r.raise_for_status()
        print(r.json())

            
            