.. _page-webapp:

Running the web app
===================

Once a classifier is trained, you can run the web app. This requires supplying
the filenames to the various preprocessed files and the Solr collection name via environment
variables. You can run the application locally for development as follows::

   export TAPIOCA_BOW="my_language_model.pkl"
   export TAPIOCA_PAGERANK="my_pagerank.npy"
   export TAPIOCA_CLASSIFIER="my_classifier.pkl"
   export TAPIOCA_COLLECTION="my_solr_collection"
   python app.py 

For production deployment, you should use a proper web server with WSGI support.

