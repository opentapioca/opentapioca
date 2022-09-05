import json
import logging
import os

import bottle
from bottle import abort, default_app, request, response, route, run, static_file
from pynif import NIFCollection

from opentapioca.classifier import SimpleTagClassifier
from opentapioca.languagemodel import BOWLanguageModel
from opentapioca.settings import (
    CLASSIFIER_PATH,
    LANGUAGE_MODEL_PATH,
    PAGERANK_PATH,
    SOLR_COLLECTION,
)
from opentapioca.tagger import Tagger
from opentapioca.wikidatagraph import WikidataGraph

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
)

tapioca_dir = os.path.dirname(__file__)

bow = BOWLanguageModel()
if LANGUAGE_MODEL_PATH:
    bow.load(LANGUAGE_MODEL_PATH)
graph = WikidataGraph()
if PAGERANK_PATH:
    graph.load_pagerank(PAGERANK_PATH)
tagger = None
classifier = None
if SOLR_COLLECTION:
    tagger = Tagger(SOLR_COLLECTION, bow, graph)
    classifier = SimpleTagClassifier(tagger)
    if CLASSIFIER_PATH:
        classifier.load(CLASSIFIER_PATH)


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
        callback = args.get("callback")
        status_code = 200
        try:
            result = view(args, *posargs, **kwargs)
        except (KeyError) as e:  # ValueError, AttributeError, KeyError) as e:
            import sys
            import traceback

            traceback.print_exc(file=sys.stdout)
            result = {"status": "error", "message": "invalid query", "details": str(e)}
            status_code = 403
        if callback:
            result = "%s(%s);" % (callback, json.dumps(result))

        if status_code == 200:
            return result
        else:
            abort(status_code, result)

    return wrapped


@route("/api/annotate", method=["GET", "POST"])
@jsonp
def annotate_api(args):
    text = args["query"]
    if not classifier:
        mentions = tagger.tag_and_rank(text)
    else:
        mentions = classifier.create_mentions(text)
        classifier.classify_mentions(mentions)

    return {"text": text, "annotations": [m.json() for m in mentions]}


@route("/api/nif", method=["GET", "POST"])
def nif_api(*args, **kwargs):
    content_format = request.headers.get("Content") or "application/x-turtle"
    content_type_to_format = {
        "application/x-turtle": "turtle",
        "text/turtle": "turtle",
    }
    nif_body = request.body.read()
    nif_doc = NIFCollection.loads(nif_body)
    for context in nif_doc.contexts:
        logger.debug(context.mention)
        mentions = classifier.create_mentions(context.mention)
        classifier.classify_mentions(mentions)
        for mention in mentions:
            mention.add_phrase_to_nif_context(context)

    response.set_header("content-type", content_format)
    return nif_doc.dumps()


@route("/")
def home():
    return static_file("index.html", root=os.path.join(tapioca_dir, "../html/"))


@route("/css/<fname>")
def css(fname):
    return static_file(fname, root=os.path.join(tapioca_dir, "../html/css/"))


@route("/js/<fname>")
def js(fname):
    return static_file(fname, root=os.path.join(tapioca_dir, "../html/js/"))


if __name__ == "__main__":
    run(host="0.0.0.0", port=8457, debug=True)

bottle.debug(True)
app = application = default_app()
