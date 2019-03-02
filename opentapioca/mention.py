

class Mention(object):
    """
    A mention is a phrase which can be associated
    with various candidate items (tags).
    """

    def __init__(self, phrase, start, end, tags, log_likelihood):
        """
        The log likelihood is the log likelihood of the phrase
        as estimated by the language model.
        """
        self.phrase = phrase
        self.start = start
        self.end = end
        self.tags = tags
        self.log_likelihood = log_likelihood
        self.best_qid = None

    def json(self):
        return {
            'start': self.start,
            'end': self.end,
            'tags': [ tag.json() for tag in self.tags ],
            'best_qid': self.best_qid,
            'log_likelihood': self.log_likelihood,
        }

    def key(self):
        """
        Returns a hashable key to identify the mention, distinguishing
        it from other mentions in the same phrase.
        """
        return (self.start, self.end)

    def tag_key(self, qid):
        """
        Returns a hashable key to identify a tag in this mention
        with the given qid.
        """
        return (self.start, self.end, qid)

    def add_phrase_to_nif_context(self, context, only_matching=True):
        """
        Adds this mention as a NIF annotation in a document.
        By default, only adds NIF phrases for matching tags, not for
        all candidates.
        """
        if self.best_qid and only_matching:
            context.add_phrase(
                beginIndex=self.start,
                endIndex=self.end,
                taIdentRef='http://www.wikidata.org/entity/'+self.best_qid)
        elif not only_matching:
            for tag in self.tags:
                context.add_phrase(
                    beginIndex=self.start,
                    endIndex=self.end,
                    taIdentRef='http://www.wikidata.org/entity/'+tag.id)

    def __repr__(self):
        return '<Mention "{}">'.format(self.phrase)

