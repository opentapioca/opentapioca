
import click

from opentapioca.wikidatagraph import WikidataGraph

@click.group()
def cli():
    pass

@click.command()
def preprocess(fname):
    """
    Preprocesses a Wikidata .json.bz2 dump into a TSV format representing its adjacency matrix.
    """
    g = WikidataGraph()
    g.preprocess_dump(fname, '.'.join(fname.split('.')[:-2]+["unsorted.tsv"]))

@click.command()
def compile(fname):
    """
    Compiles a sorted preprocessed Wikidata dump in TSV format to a Numpy sparse matrix.
    """
    g = WikidataGraph()
    g.load_from_preprocessed_dump(fname)
    g.save_matrix('.'.join(fname.split('.')[:-1]+['npz']))

@click.command()
def compute_pagerank(fname):
    """
    Computes the pagerank of a Wikidata adjacency matrix as represented by a Numpy sparse matrix in NPZ format.
    """
    g = WikidataGraph()
    fname = sys.argv[1]
    g.load_from_matrix(fname)
    g.compute_pagerank()
    g.save_pagerank('.'.join(fname.split('.')[:-1] + ['pgrank.npy']))

@click.command()
def index_dump(collection_name, fname, solr='http://localhost:8983/solr/'):
    """
    Indexes a Wikidata dump in a new Solr collection with the given name.
    """
    g = TaggerFactory(solr)
    try:
        g.create_collection(collection_name)
    except CollectionAlreadyExists:
        pass
    g.index_wd_dump(collection_name, fname)
    
cli.add_command(preprocess)
cli.add_command(compile)
cli.add_command(compute_pagerank)
cli.add_command(index_dump)

if __name__ == '__main__':
    cli()
