import bz2
import json
import sys
from opentapioca.wditem import WikidataItemDocument

class WikidataDumpReader(object):
    def __init__(self, fname):
        self.fname = fname
        if fname == '-':
            self.f = sys.stdin
        else:
            self.f = bz2.open(fname, mode='rt', encoding='utf-8')

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.fname != '-':
            self.f.close()

    def __iter__(self):
        for line in self.f:
            try:
                # remove the trailing comma
                line = line[:-2]
                item = json.loads(line)
                yield WikidataItemDocument(item)
            except ValueError as e:
                continue


