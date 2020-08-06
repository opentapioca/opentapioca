.. _page-webapp:

Running the web app
===================

Once a classifier is trained, you can run the web app. This requires supplying
the filenames to the various preprocessed files and the Solr collection name in the
``settings.py`` file. A template for this file is provided as ``settings_template.py``.
You can then run the application locally for development as follows::

   python app.py 

This will expose a development web server at http://localhost:8457/.

For production deployment, you should use a proper web server with WSGI support.

Keeping in sync with Wikidata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can keep up to date with Wikidata by listening to its stream of edits, which will keep your Solr collection in sync::

    tapioca index-stream -p profiles/human_organization_location.json my_solr_collection

This command has other options, use `tapioca index-stream --help` for a description of those.
This will not update the PageRank and the language model, which are not expected to evolve quickly. You can refresh those from time to time with fresh dumps.
