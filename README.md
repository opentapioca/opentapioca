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

In a Virtualenv, do `pip install -r requirements.txt` to install the Python dependencies.

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
```
python read_graph.py preprocess latest-all.json.bz2
sort -n -k 1 latest-all.unsorted.tsv > wikidata_graph.tsv
python read_graph.py compile wikidata_graph.tsv
```

This creates a `wikidata_graph.npz` that stores the Wikidata graph in a sparse adjacency matrix in Numpy format.
We can use it to compute the pagerank of items in this graph:

```
python compute_pagerank.py wikidata_graph.npz
```

Third, we will index the Wikidata dump: TODO 


Running tests
-------------

OpenTapioca comes with a test suite that can be run with `pytest`. This
requires a SolrCloud server to be running on `localhost:8983`.

