.. _page-install:

Installing OpenTapioca
======================

This software is a Python web service that requires Solr.

Installing Solr
--------------

It relies 
on a recent new feature of Solr (since 7.4.0), which was previously available as 
an external plugin, `SolrTextTagger <https://github.com/OpenSextant/SolrTextTagger>`__.
If you cannot use a recent Solr version, it is possible to use older versions with the plugin
installed: this will require changing the class names in the Solr configs (in the ``configset`` directory).

Install `Solr <https://lucene.apache.org/solr/>`__ 7.4.0 or above.

OpenTapioca requires that Solr runs in Cloud mode, so you can start it as follows:

::

   bin/solr start -c -m 4g

The memory available to Solr (here 4 GB) will determine how many indexing operations you can run in parallel
(searching is cheap).

In its Cloud mode, Solr reads the configuration for its indices from so-called "configsets" which gouvern the
configuration of multiple collections. OpenTapioca comes with the appropriate configsets for its collections
and the default one is called "tapioca". You need to upload it to Solr before indexing any data, as follows:

::

   bin/solr zk -upconfig -z localhost:9983 -n tapioca -d configsets/tapioca

Custom analyzers
~~~~~~~~~~~~~~~~

Some profiles require custom Solr analyzers and tokenizers. For instance
the Twitter profile can be used to index Twitter usernames and hashtags
as labels, which is useful to annotate mentions in Twitter feeds. This
requires a special tokenizer which handles these tokens appropriately.
This tokenizer is provided as a Solr plugin in the ``plugins``
directory. It can be installed by adding this jar in the
``server/solr/lib`` directory of your Solr instance (the ``lib``
subfolder needs to be created first).


Installing Python dependencies
------------------------------

OpenTapioca is known to work with Python 3.6, and offers a command-line interface
to manipulate Wikidata dumps and train classifiers from datasets.

In a Virtualenv, do ``pip install -r requirements.txt`` to install the
Python dependencies, and ``python setup.py install`` to install the CLI
in your PATH.

When developing OpenTapioca, you can use `pip install -e .` to install the CLI
from the local files, so that your changes on the source code are directly reflected
in the CLI, without the need to run ``python setup.py install`` every time you change
something.

