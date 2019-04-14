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

