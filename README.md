OpenTapioca
===========
[![Documentation Status](https://readthedocs.org/projects/opentapioca/badge/?version=latest)](https://opentapioca.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/wetneb/opentapioca.svg?branch=master)](https://travis-ci.org/wetneb/opentapioca) [![Coverage Status](https://coveralls.io/repos/github/wetneb/opentapioca/badge.svg)](https://coveralls.io/github/wetneb/opentapioca)

Simple entity linking system for Wikidata.

Setup
-----

This software is a Python web service that requires Solr with SolrTextTagger.

Install [Solr](https://lucene.apache.org/solr/) 7.4.0 or above.

Run SolrCloud:

```
bin/solr start -c -m 4g
```

Upload Solr configuration set to ZooKeeper:
```
bin/solr zk -upconfig -z localhost:9983 -n tapioca -d configsets/tapioca
```

In a Virtualenv, do `pip install -r requirements.txt` to install the Python dependencies,
and `python setup.py install` to install the CLI in your PATH.

Training process
----------------

Various components need to be trained in order to obtain a functional tagger. First, download
a Wikidata JSON dump compressed in `.bz2` format:
```
wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2
```

We will first use this dump to train a bag of words language model:
```
tapioca train-bow latest-all.json.bz2
```

This will create a `bow.pkl` file which counts the number of occurences
of words in Wikidata labels.

Second, we will use the dump to extract a more compact graph of entities that can be stored
in memory. This will be used to compute the pagerank of items in this graph.
We convert a Wikidata dump into an adjacency matrix and a pagerank vector
in four steps:
1. preprocess the dump, only extracting the information we need: this
   creates a TSV file containing on each line the item id (without leading Q),
   the list of ids this item points to, and the number of occurences of such links.
   ```
   tapioca preprocess latest-all.json.bz2
   ```

2. this dump must be externally sorted (for instance with GNU sort). Doing
   the sorting externally is more efficient than doing it inside Python itself.
   ```
   sort -n -k 1 latest-all.unsorted.tsv > wikidata_graph.tsv
   ```

3. the sorted dump is converted into a Numpy sparse adjacency matrix `wikidata_graph.npz`
   ```
   tapioca compile wikidata_graph.tsv
   ```

4. we can compute the pagerank from the Numpy sparse matrix and store 
   it as a dense matrix `wikidata_graph.pgrank.npy`
   ```
   tapioca compute-pagerank wikidata_graph.npz
   ```
    
This slightly convoluted setup makes it possible to compute the adjacency matrix and pagerank
from entire dumps on a machine with little memory (8GB).

We then need to index the Wikidata dump in a Solr collection. This uses the JSON dump only.
This also requires creating an indexing profile, which defines which items will be indexed and how.
A sample profile is provided to index people, organizations and places at `profiles/human_organization_place.json`:
```
{
    "language": "en", # The preferred language
    "name": "human_organization_location", # An identifier for the profile
    "restrict_properties": [
        "P2427", "P1566", "P496", # Include all items bearing any of these properties
    ],
    "restrict_types": [
        # Include all items with any of these types, or subclasses of them
        {"type": "Q43229", "property": "P31"},
        {"type": "Q618123", "property": "P31"},
        {"type": "Q5", "property": "P31"}
    ],
    "alias_properties": [
        # Add as alias the values of these properties
        {"property": "P496", "prefix": null},
        {"property": "P2002", "prefix": "@"},
        {"property": "P4550", "prefix": null}
    ]
}
```

Pick a Solr collection name and run:
```
tapioca index-dump my_collection_name latest-all.json.bz2 --profile profiles/human_organization_place.json
```
Note that if you have multiple cores available, you might want to run decompression as a separate
process, given that it is generally the bottleneck:
```
bunzip2 < latest-all.json.bz2 | tapioca index-dump my_collection_name - --profile profiles/human_organization_place.json
```

Custom analyzers
----------------

Some profiles require custom Solr analyzers and tokenizers. For instance the Twitter profile can be used
to index Twitter usernames and hashtags as labels, which is useful to annotate mentions in Twitter feeds.
This requires a special tokenizer which handles these tokens appropriately. This tokenizer is provided as 
a Solr plugin in the `plugins` directory. It can be installed by adding this jar in the `server/solr/lib` directory
of your Solr instance (the `lib` subfolder needs to be created first).

Running tests
-------------

OpenTapioca comes with a test suite that can be run with `pytest`. This
requires a SolrCloud server to be running on `localhost:8983`.


