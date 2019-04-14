
# The name of the Solr collection where Wikidata is indexed
SOLR_COLLECTION = 'wd_2019-02-24'

# The path to the language model, trained with "tapioca train-bow"
LANGUAGE_MODEL_PATH='data/wd_2019-02-24.bow.pkl'
# The path to the pagerank Numpy vector, computed with "tapioca compute-pagerank"
PAGERANK_PATH='data/wd_2019-02-24.pgrank.npy'
# The path to the trained classifier, obtained from "tapioca train-classifier"
CLASSIFIER_PATH='data/rss_istex_classifier.pkl'
