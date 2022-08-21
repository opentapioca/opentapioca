# The name of the Solr collection where Wikidata is indexed
SOLR_COLLECTION = None

# The path to the language model, trained with "tapioca train-bow"
LANGUAGE_MODEL_PATH = None

# The path to the pagerank Numpy vector, computed with "tapioca compute-pagerank"
PAGERANK_PATH = None

# The path to the trained classifier, obtained from "tapioca train-classifier"
CLASSIFIER_PATH = None

SOLR_HOST = "localhost"
SOLR_PORT = 8983
SOLR_ENDPOINT = f"http://{SOLR_HOST}:{SOLR_PORT}/solr/"
