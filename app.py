from bottle import route, run, default_app, static_file, request, abort, response
import bottle
import sys
import json
import os
from pynif import NIFCollection
import logging
import settings

from opentapioca.wikidatagraph import WikidataGraph
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.tagger import Tagger
from opentapioca.classifier import SimpleTagClassifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

tapioca_dir = os.path.dirname(__file__)

bow = BOWLanguageModel()
if settings.LANGUAGE_MODEL_PATH:
    bow.load(settings.LANGUAGE_MODEL_PATH)
graph = WikidataGraph()
if settings.PAGERANK_PATH:
    graph.load_pagerank(settings.PAGERANK_PATH)
tagger = None
classifier = None
if settings.SOLR_COLLECTION:
    tagger = Tagger(settings.SOLR_COLLECTION, bow, graph)
    classifier = SimpleTagClassifier(tagger)
    if settings.CLASSIFIER_PATH:
        classifier.load(settings.CLASSIFIER_PATH)

def jsonp(view):
    """
    Decorator for views that return JSON
    """
    def wrapped(*posargs, **kwargs):
        args = {}
        # if we access the args via get(),
        # we can get encoding errors...
        for k in request.forms:
            args[k] = getattr(request.forms, k)
        for k in request.query:
            args[k] = getattr(request.query, k)
        callback = args.get('callback')
        status_code = 200
        try:
            result = view(args, *posargs, **kwargs)
        except (KeyError) as e:#ValueError, AttributeError, KeyError) as e:
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            result = {'status':'error',
                    'message':'invalid query',
                    'details': str(e)}
            status_code = 403
        if callback:
            result = '%s(%s);' % (callback, json.dumps(result))

        if status_code == 200:
            return result
        else:
            abort(status_code, result)

    return wrapped


@route('/api/annotate', method=['GET','POST'])
@jsonp
def annotate_api(args):
    text = args['query']
    if not classifier:
        mentions = tagger.tag_and_rank(text)
    else:
        mentions = classifier.create_mentions(text)
        classifier.classify_mentions(mentions)

    return {
        'text':text,
        'annotations': [m.json() for m in mentions]
    }

@route('/api/nif', method=['GET','POST'])
def nif_api(*args, **kwargs):
    content_format = request.headers.get('Content') or 'application/x-turtle'
    content_type_to_format = {
        'application/x-turtle': 'turtle',
        'text/turtle': 'turtle',
    }
    # for backwards compatibility we assume that only_matching=true by default
    only_matching = request.GET.get('only_matching', 'true') == 'true'

    nif_body = request.body.read()
    nif_doc = NIFCollection.loads(nif_body)
    for context in nif_doc.contexts:
        logger.debug(context.mention)
        mentions = classifier.create_mentions(context.mention)
        classifier.classify_mentions(mentions)
        for mention in mentions:
            mention.add_phrase_to_nif_context(context, only_matching=only_matching)

    response.set_header('content-type', content_format)
    return nif_doc.dumps()

@route('/')
def home():
    return static_file('index.html', root=os.path.join(tapioca_dir, 'html/'))

@route('/css/<fname>')
def css(fname):
    return static_file(fname, root=os.path.join(tapioca_dir, 'html/css/'))

@route('/js/<fname>')
def js(fname):
    return static_file(fname, root=os.path.join(tapioca_dir, 'html/js/'))

if __name__ == '__main__':
    run(host='0.0.0.0', port=8457, debug=True)

# bottle.debug(True)
app = application = default_app()
