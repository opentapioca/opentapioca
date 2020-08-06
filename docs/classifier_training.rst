.. _page-classifier_training:

Training a classifier
=====================

Once a Wikidata dump is preprocessed and indexed, we can train a classifier
to predict matches in text.

Getting a NIF dataset
---------------------

Training requires access to a dataset encoded in `NIF (Natural Language Interchange Format) <https://github.com/dice-group/gerbil/wiki/NIF>`__.
Various such datasets can be found at the `NLP2RDF dashboard <http://dashboard.nlp2rdf.aksw.org/>`__ (`archived version <https://web.archive.org/web/20190913203545/http://dashboard.nlp2rdf.aksw.org/>`_).
The NIF dataset is required to use Wikidata entity URIs for its annotations. Here is an example of what it looks like in the flesh::

   <https://zenodo.org/wd_affiliations/4> a nif:Context,
         nif:OffsetBasedString ;
      nif:beginIndex "0"^^xsd:nonNegativeInteger ;
      nif:endIndex "67"^^xsd:nonNegativeInteger ;
      nif:isString "Konarka Technologies, 116 John St., Suite 12, Lowell, MA 01852, USA" ;
      nif:sourceUrl <https://doi.org/10.1002/aenm.201100390> .

   <https://zenodo.org/wd_affiliations/4#offset_64_67> a nif:OffsetBasedString,
         nif:Phrase ;
      nif:anchorOf "USA" ;
      nif:beginIndex "64"^^xsd:nonNegativeInteger ;
      nif:endIndex "67"^^xsd:nonNegativeInteger ;
      nif:referenceContext <https://zenodo.org/wd_affiliations/4> ;
      itsrdf:taIdentRef <http://www.wikidata.org/entity/Q30> .


Converting an existing dataset from a custom format to NIF can be done using the `pynif <https://github.com/wetneb/pynif>`_ Python library.
This library can be used to generate and parse NIF datasets with a simple API.

Annotating your own dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to annotate your own dataset, you could use an existing annotator such as `NIFIFY <https://github.com/henryrosalesmendez/NIFify_v2>`__ (although it currently does not seem to handle large datasets very well).


Converting an existing NIF dataset to Wikidata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have an existing dataset with URIs pointing to another knowledge base, such as DBpedia, you can convert it to Wikidata.
This will first require translating existing annotations, which can be done automatically with tools such as `nifconverter <https://github.com/wetneb/nifconverter>`__. Then comes the harder part: you need to annotate any mention of an entity which is not
covered by the original knowledge base, but is included in Wikidata. If out-of-KB mentions are already annotated in your dataset,
then you can extract these and use tools such as `OpenRefine <http://openrefine.org>`__ to match their phrases to Wikidata. Otherwise, you can extract them with a named entity recognition tool, or annotate them manually.


Training with cross-validation
------------------------------

Training a classifier on a dataset is done via the CLI, as follows::

   tapioca train-classifier -c my_solr_collection -b my_language_model.pkl -p my_pagerank.npy -d my_dataset.ttl -o my_classifier.pkl

This will save the classifier as ``my_classifier.pkl``, which can then be used to tag text in the web app.
