import logging
import os

import click
import dateutil.parser
from pynif import NIFCollection

from opentapioca.classifier import SimpleTagClassifier
from opentapioca.indexingprofile import IndexingProfile
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.readers.dumpreader import WikidataDumpReader
from opentapioca.readers.sparqlreader import SparqlReader
from opentapioca.readers.streamreader import WikidataStreamReader
from opentapioca.tagger import Tagger
from opentapioca.taggerfactory import CollectionAlreadyExists, TaggerFactory
from opentapioca.wikidatagraph import WikidataGraph


@click.group()
def cli():
    logging.basicConfig(
        level=os.environ.get("TAPIOCA_LOGLEVEL", "INFO"),
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )
    pass


@click.command()
@click.argument("filename")
@click.option(
    "-o", "--outfile", default=None, help="Output file to save the language model to."
)
def train_bow(filename, outfile):
    """
    Trains a bag of words language model from the terms of the entities in a dump.
    """
    if outfile is None:
        offset = 2 if filename.endswith(".json.bz2") else 1
        outfile = ".".join(filename.split(".")[:-offset] + ["bow.pkl"])
    bow = BOWLanguageModel.train_from_dump(filename)
    bow.save(outfile)


@click.command()
@click.argument("filename")
def bow_shell(filename):
    """
    Interactively evaluates a language model on chosen phrases
    """
    bow = BOWLanguageModel()
    bow.load(filename)
    while True:
        phrase = input(">>> ")
        print(bow.log_likelihood(phrase))


@click.command()
@click.argument("filename")
@click.option(
    "-o",
    "--outfile",
    default=None,
    help="Output file to save the preprocessed graph to.",
)
def preprocess(filename, outfile):
    """
    Preprocesses a Wikidata .json.bz2 dump into a TSV format representing its adjacency matrix.
    """
    if outfile is None:
        outfile = ".".join(filename.split(".")[:-2] + ["unsorted.tsv"])
    g = WikidataGraph()
    g.preprocess_dump(filename, outfile)


@click.command()
@click.argument("filename")
@click.option(
    "-o", "--outfile", default=None, help="Output file to save the adjacency matrix to."
)
def compile(filename, outfile):
    """
    Compiles a sorted preprocessed Wikidata dump in TSV format to a Numpy sparse matrix.
    """
    if outfile is None:
        outfile = ".".join(filename.split(".")[:-1] + ["npz"])
    g = WikidataGraph()
    g.load_from_preprocessed_dump(filename)
    g.save_matrix(outfile)


@click.command()
@click.argument("filename")
@click.option(
    "-o", "--outfile", default=None, help="Output file to save the pagerank vector to."
)
def compute_pagerank(filename, outfile):
    """
    Computes the pagerank of a Wikidata adjacency matrix as represented by a Numpy sparse matrix in NPZ format.
    """
    if outfile is None:
        outfile = ".".join(filename.split(".")[:-1] + ["pgrank.npy"])
    g = WikidataGraph()
    g.load_from_matrix(filename)
    g.compute_pagerank()
    g.save_pagerank(outfile)


@click.command()
@click.argument("filename")
def pagerank_shell(filename):
    """
    Interactively retrieve the pagerank on chosen items
    """
    g = WikidataGraph()
    g.load_pagerank(filename)
    while True:
        qid = input(">>> ")
        print(g.get_pagerank(qid))


@click.command()
@click.argument("collection_name")
@click.argument("filename")
@click.option("-p", "--profile", help="Filename of the indexing profile to use")
@click.option(
    "-s",
    "--shards",
    default=1,
    help="Number of shards to use when creating the collection, if needed",
)
@click.option(
    "-k",
    "--skip",
    default=0,
    help="Number of documents to skip because they are already indexed",
)
def index_dump(collection_name, filename, profile, shards, skip):
    """
    Indexes a Wikidata dump in a new Solr collection with the given name.
    """
    tagger = TaggerFactory()
    indexing_profile = IndexingProfile.load(profile)
    try:
        tagger.create_collection(
            collection_name, num_shards=shards, configset=indexing_profile.solrconfig
        )
    except CollectionAlreadyExists:
        pass
    dump = WikidataDumpReader(filename)
    tagger.index_stream(
        collection_name,
        dump,
        indexing_profile,
        batch_size=2000,
        commit_time=10,
        delete_excluded=False,
        skip_docs=skip,
    )


@click.command()
@click.argument("collection_name")
@click.argument("sparql_query_file")
@click.option("-p", "--profile", help="Filename of the indexing profile to use")
@click.option(
    "-s",
    "--shards",
    default=1,
    help="Number of shards to use when creating the collection, if needed",
)
def index_sparql(collection_name, sparql_query_file, profile, shards):
    """
    Indexes the results of a SPARQL query which contains an "item" variable pointing to items to index
    """
    tagger = TaggerFactory()
    indexing_profile = IndexingProfile.load(profile)
    try:
        tagger.create_collection(
            collection_name, num_shards=shards, configset=indexing_profile.solrconfig
        )
    except CollectionAlreadyExists:
        pass
    with open(sparql_query_file, "r") as f:
        query = f.read()
    query_results = SparqlReader(query)
    tagger.index_stream(
        collection_name,
        query_results,
        indexing_profile,
        batch_size=50,
        commit_time=10,
        delete_excluded=False,
    )


@click.command()
@click.argument("collection_name")
@click.option("-p", "--profile", help="Filename of the indexing profile to use")
@click.option(
    "-s",
    "--shards",
    default=1,
    help="Number of shards to use when creating the collection, if needed",
)
@click.option(
    "-a",
    "--after",
    default=None,
    help="Start indexing the stream after the given point in time (in the past)",
)
def index_stream(collection_name, profile, shards, after):
    """
    Listens to the Wikidata edit stream and updates a collection according to
    the given indexing profile.
    """
    tagger = TaggerFactory()
    indexing_profile = IndexingProfile.load(profile)
    try:
        tagger.create_collection(
            collection_name, num_shards=shards, configset=indexing_profile.solrconfig
        )
    except CollectionAlreadyExists:
        pass
    if after is not None:
        after = dateutil.parser.parse(after)
    stream = WikidataStreamReader(from_time=after)
    tagger.index_stream(
        collection_name,
        stream,
        indexing_profile,
        batch_size=50,
        commit_time=1,
        delete_excluded=True,
    )


@click.command()
@click.argument("collection_name")
def delete_collection(collection_name):
    tagger = TaggerFactory()
    tagger.delete_collection(collection_name)


@click.command()
@click.option(
    "-c",
    "--collection",
    default=None,
    help="Name of the Solr collection where Wikidata is indexed.",
)
@click.option(
    "-b",
    "--bow",
    default=None,
    help="Path of the trained bag of words language model (.pkl file)",
)
@click.option(
    "-p", "--pagerank", default=None, help="Path of the trained PageRank (.npy file)"
)
@click.option(
    "-d",
    "--dataset",
    default=None,
    help="Path to the NIF dataset to use as training dataset.",
)
@click.option(
    "-o",
    "--output",
    default=None,
    help="Path where the trained classifier should be written.",
)
@click.option(
    "-m",
    "--max-iter",
    default=500,
    help="Maximum number of iterations for SVM training.",
)
def train_classifier(collection, bow, pagerank, dataset, output, max_iter):
    """
    Trains a tag classifier on a NIF dataset.
    """
    if output is None:
        output = "trained_classifier.pkl"
    b = BOWLanguageModel()
    b.load(bow)
    graph = WikidataGraph()
    graph.load_pagerank(pagerank)
    tagger = Tagger(collection, b, graph)
    d = NIFCollection.load(dataset)
    clf = SimpleTagClassifier(tagger)
    max_iter = int(max_iter)

    parameter_grid = []
    for max_distance in [50, 75, 150, 200]:
        for similarity, beta in [
            ("one_step", 0.2),
            ("one_step", 0.1),
            ("one_step", 0.3),
        ]:
            for C in [10.0, 1.0, 0.1]:
                for smoothing in [0.8, 0.6, 0.5, 0.4, 0.3]:
                    parameter_grid.append(
                        {
                            "nb_steps": 4,
                            "max_similarity_distance": max_distance,
                            "C": C,
                            "similarity": similarity,
                            "beta": beta,
                            "similarity_smoothing": smoothing,
                        }
                    )

    best_params = clf.crossfit_model(d, parameter_grid, max_iter=max_iter)
    print("#########")
    print(best_params)
    clf.save(output)


cli.add_command(train_bow)
cli.add_command(bow_shell)
cli.add_command(preprocess)
cli.add_command(compile)
cli.add_command(compute_pagerank)
cli.add_command(pagerank_shell)
cli.add_command(index_dump)
cli.add_command(index_sparql)
cli.add_command(index_stream)
cli.add_command(delete_collection)
cli.add_command(train_classifier)

if __name__ == "__main__":
    cli()
