
import click

from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.taggerfactory import TaggerFactory
from opentapioca.taggerfactory import CollectionAlreadyExists
from opentapioca.tagger import Tagger
from opentapioca.classifier import SimpleTagClassifier
from pynif import NIFCollection

@click.group()
def cli():
    pass

@click.command()
@click.argument('filename')
@click.option('-o', '--outfile', default=None, help='Output file to save the language model to.')
def train_bow(filename, outfile):
    """
    Trains a bag of words language model from the terms of the entities in a dump.
    """
    if outfile is None:
        offset = 2 if filename.endswith('.json.bz2') else 1
        outfile = '.'.join(filename.split('.')[:-offset]+['bow.pkl'])
    bow = BOWLanguageModel.train_from_dump(filename)
    bow.save(outfile)

@click.command()
@click.argument('filename')
def bow_shell(filename):
    """
    Interactively evaluates a language model on chosen phrases
    """
    bow = BOWLanguageModel()
    bow.load(filename)
    while True:
        phrase = input('>>> ')
        print(bow.log_likelihood(phrase))

@click.command()
@click.argument('filename')
@click.option('-o', '--outfile', default=None, help='Output file to save the preprocessed graph to.')
def preprocess(filename, outfile):
    """
    Preprocesses a Wikidata .json.bz2 dump into a TSV format representing its adjacency matrix.
    """
    if outfile is None:
        outfile = '.'.join(filename.split('.')[:-2]+["unsorted.tsv"])
    g = WikidataGraph()
    g.preprocess_dump(filename, outfile)

@click.command()
@click.argument('filename')
@click.option('-o', '--outfile', default=None, help='Output file to save the adjacency matrix to.')
def compile(filename, outfile):
    """
    Compiles a sorted preprocessed Wikidata dump in TSV format to a Numpy sparse matrix.
    """
    if outfile is None:
        outfile = '.'.join(filename.split('.')[:-1]+['npz'])
    g = WikidataGraph()
    g.load_from_preprocessed_dump(filename)
    g.save_matrix(outfile)

@click.command()
@click.argument('filename')
@click.option('-o', '--outfile', default=None, help='Output file to save the pagerank vector to.')
def compute_pagerank(filename, outfile):
    """
    Computes the pagerank of a Wikidata adjacency matrix as represented by a Numpy sparse matrix in NPZ format.
    """
    if outfile is None:
        outfile = '.'.join(filename.split('.')[:-1] + ['pgrank.npy'])
    g = WikidataGraph()
    g.load_from_matrix(filename)
    g.compute_pagerank()
    g.save_pagerank(outfile)

@click.command()
@click.argument('filename')
def pagerank_shell(filename):
    """
    Interactively retrieve the pagerank on chosen items
    """
    g = WikidataGraph()
    g.load_pagerank(filename)
    while True:
        qid = input('>>> ')
        print(g.get_pagerank(qid))


@click.command()
@click.argument('collection_name')
@click.argument('filename')
@click.option('-t', '--types', default=None, help='Types to restrict the index to (comma separated qids)')
@click.option('-p', '--properties', default=None, help='Restrict the index to items bearings the given properties (comma separated pids)')
def index_dump(collection_name, filename, types, properties, solr='http://localhost:8983/solr/'):
    """
    Indexes a Wikidata dump in a new Solr collection with the given name.
    """
    g = TaggerFactory(solr)
    type_list = None
    if types is not None:
        type_list = types.split(',')
    properties_list = None
    if properties is not None:
        properties_list = properties.split(',')
    try:
        g.create_collection(collection_name)
    except CollectionAlreadyExists:
        pass
    g.index_wd_dump(collection_name, filename, restrict_type=type_list, restrict_property=properties_list)

@click.command()
@click.argument('collection_name')
def delete_collection(collection_name, solr='http://localhost:8983/solr/'):
    g = TaggerFactory(solr)
    g.delete_collection(collection_name)

@click.command()
@click.option('-c', '--collection', default=None, help='Name of the Solr collection where Wikidata is indexed.')
@click.option('-b', '--bow', default=None, help='Path of the trained bag of words language model (.pkl file)')
@click.option('-p', '--pagerank', default=None, help='Path of the trained PageRank (.npy file)')
@click.option('-d', '--dataset', default=None, help='Path to the NIF dataset to use as training dataset.')
@click.option('-o', '--output', default=None, help='Path where the trained classifier should be written.')
def train_classifier(collection, bow, pagerank, dataset, output):
    """
    Trains a tag classifier on a NIF dataset.
    """
    if output is None:
        output = 'trained_classifier.pkl'
    b = BOWLanguageModel()
    b.load(bow)
    graph = WikidataGraph()
    graph.load_pagerank(pagerank)
    tagger = Tagger(collection, b, graph)
    d = NIFCollection.load(dataset)
    clf = SimpleTagClassifier(tagger)

    parameter_grid = []
    for mode in ['markov']:
        for nb_steps in [1, 2, 4]:
            for C in [50.0, 10.0, 1.0, 0.1, 0.01, 0.001, 0.0001]:
                parameter_grid.append({
                    'nb_steps':nb_steps,
                    'alpha':alpha,
                    'C': C,
                    'mode': mode,
                    })

    best_params = clf.crossfit_model(d, parameter_grid)
    print('#########')
    print(best_params)
    clf.save(output)

cli.add_command(train_bow)
cli.add_command(bow_shell)
cli.add_command(preprocess)
cli.add_command(compile)
cli.add_command(compute_pagerank)
cli.add_command(pagerank_shell)
cli.add_command(index_dump)
cli.add_command(delete_collection)
cli.add_command(train_classifier)

if __name__ == '__main__':
    cli()
