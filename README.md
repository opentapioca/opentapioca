OpenTapioca
===========

Simple entity linking system for Wikidata.

Setup
-----

This software is a Python web service that requires Solr with SolrTextTagger.

Install [Solr](https://lucene.apache.org/solr/) 7.4.0 or above.

Run SolrCloud:

```
bin/solr -e cloud
```

Upload Solr configuration set to ZooKeeper:
```
bin/solr zk -upconfig -z localhost:9983 -n affilations -d configsets/affiliations
```

In a Virtualenv, do `pip install -r requirements.txt` to install the Python dependencies,
and `python setup.py install` to install the CLI in your PATH.

Training process
----------------

TODO: make language configurable
TODO: make types configurable
TODO: make list of additional properties to pull in as labels configurable (Twitter ID) with format

Various components need to be trained in order to obtain a functional tagger. First, download
a Wikidata JSON dump compressed in `.bz2` format:
```
wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2
```

We will first use this dump to train a bag of words language model:
```
python opentapioca/languagemodel.py latest-all.json.bz2
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
   python read_graph.py preprocess latest-all.json.bz2
   ```

2. this dump must be externally sorted (for instance with GNU sort). Doing
   the sorting externally is more efficient than doing it inside Python itself.
   ```
   sort -n -k 1 latest-all.unsorted.tsv > wikidata_graph.tsv
   ```

3. the sorted dump is converted into a Numpy sparse adjacency matrix `wikidata_graph.npz`
   ```
   python read_graph.py compile wikidata_graph.tsv
   ```

4. we can compute the pagerank from the Numpy sparse matrix and store 
   it as a dense matrix `wikidata_graph.pgrank.npy`
   ```
   python compute_pagerank.py wikidata_graph.npz
   ```
    
This slightly convoluted setup makes it possible to compute the adjacency matrix and pagerank
from entire dumps on a machine with little memory (8GB).

We then need to index the Wikidata dump in a Solr collection. This uses the JSON dump only. Pick
a Solr collection name and run:
```
python index_dump.py my_collection_name latest-all.json.bz2
```

Running tests
-------------

OpenTapioca comes with a test suite that can be run with `pytest`. This
requires a SolrCloud server to be running on `localhost:8983`.

