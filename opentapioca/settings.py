import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
DATA_DIR = ROOT_DIR / "data"


# The name of the Solr collection where Wikidata is indexed
SOLR_COLLECTION = os.environ.get("SOLR_COLLECTION")

# The path to the language model, trained with "tapioca train-bow"
LANGUAGE_MODEL_PATH = str(DATA_DIR / os.environ.get("LANGUAGE_MODEL_FILE"))

# The path to the pagerank Numpy vector, computed with "tapioca compute-pagerank"
PAGERANK_PATH = str(DATA_DIR / os.environ.get("PAGERANK_FILE"))

# The path to the trained classifier, obtained from "tapioca train-classifier"
CLASSIFIER_PATH = str(DATA_DIR / os.environ.get("CLASSIFIER_FILE"))


SOLR_HOST = os.environ.get("SOLR_HOST", default="solr")
SOLR_PORT = os.environ.get("SOLR_PORT", default="8983")
SOLR_ENDPOINT = f"http://{SOLR_HOST}:{SOLR_PORT}/solr/"
