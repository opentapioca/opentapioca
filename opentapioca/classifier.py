import numpy
from collections import defaultdict
from sklearn import svm
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
import pickle


class SimpleTagClassifier(object):
    """
    A linear support vector classifier to predict the validity of a mention.
    """
    def __init__(self, tagger, alpha=0.85, nb_steps=2, C=0.001, mode="markov"):
        self.tagger = tagger
        self.alpha = alpha
        self.nb_steps = nb_steps
        self.C = C
        self.mode = mode

    def feature_vectors_from_mention(self, mention):
        """
        Returns a dictionary of tag keys to feature vectors
        in a mention
        """
        dct = {}
        for tag in mention['tags']:
            feature_vector = [
                mention['log_likelihood'],
                tag['rank'],
                tag['nb_statements'],
                tag['nb_sitelinks'],
            ]
            tag_key = (mention['start'], mention['end'], tag['id'])
            dct[tag_key] = feature_vector
        return dct

       
    def load(self, fname):
        with open(fname, 'rb') as f:
            dct = pickle.load(f)
        if 'tagger' in dct:
            del dct['tagger']
        self.__dict__.update(dct)

    def save(self, fname):
        with open(fname, 'wb') as f:
            dct = dict(self.__dict__.items())
            del dct['tagger']
            pickle.dump(dct, f)

    def crossfit_model(self, dataset, parameters=None):
        """
        Learns the model and report F1 score
        with cross-validation.
        """
        k = 10
        chunks = [ set() for i in range(k) ]
        for idx, doi_doc in enumerate(dataset.doi_docs):
            chunks[idx % k].add(doi_doc)
        print([ len(chunk) for chunk in chunks])

        all_doi_docs = set(dataset.doi_docs)

        # tag all documents once and for all
        docid_to_mentions = {}
        for idx, doi_doc in enumerate(all_doi_docs):
            if idx % 100 == 0:
                print("{}...".format(idx))
            docid_to_mentions[doi_doc] = self.tagger.tag_and_rank(doi_doc[1])

        if parameters is None:
            parameters = [{}]

        best_params = {}
        best_f1 = 0.
        best_classifier = None
        for param_setting in parameters:
            # Set the parameters
            for param, val in param_setting.items():
                setattr(self, param, val)

            # Run cross-validation
            scores = defaultdict(float)
            for chunk_id in range(k):
                training_chunks = all_doi_docs - chunks[chunk_id]
                self.train_model(dataset, training_chunks, docid_to_mentions)
                chunk_scores = self.evaluate_model(dataset, chunks[chunk_id], docid_to_mentions)
                for method, score in chunk_scores.items():
                    scores[method] += score/k
            print('-----')
            print(param_setting)
            print(dict(scores.items()))
            if scores['f1'] > best_f1:
                print('(best so far)')
                best_params = param_setting
                best_f1 = scores['f1']
                # Retrain on whole dev set with these parameters
                self.train_model(dataset, all_doi_docs, docid_to_mentions)
                best_classifier = self.fit
                self.save('data/best_classifier_so_far.pkl')
            else:
                self.save('data/latest_classifier.pkl')


        self.fit = best_classifier
        return best_params, best_f1

    def train_model(self, dataset, doi_docs=None, docid_to_mentions=None):
        """
        Train the model on the given dataset, restricting
        training samples to the given doi_docs (or no restriction if None)
        """

        if doi_docs is None:
            doi_docs = dataset.doi_docs

        design_matrix = []
        classes = []
        nb_valid = 0
        for doi, doc in doi_docs:
            judgment = dataset.judgments.get((doi, doc))
            mentions = (docid_to_mentions[(doi,doc)] if docid_to_mentions
                    else self.tagger.tag_and_rank(doc))

            feature_vectors, tag_indices = self.build_feature_vectors_for_doc(mentions)

            for decision in judgment:
                tag_id = (decision['start'], decision['end'], decision['qid'])
                if tag_id in tag_indices:
                    design_matrix.append(feature_vectors[tag_indices[tag_id]])
                    valid = 1 if decision['valid'] else 0
                    classes.append(valid)
                    nb_valid += valid

        if not nb_valid:
            print('No positive sample found')
            return

        scaler = preprocessing.StandardScaler()
        clf = svm.LinearSVC(class_weight='balanced',C=self.C)
        pipeline = Pipeline([('scaler',scaler),('svm',clf)])


        fit = pipeline.fit(design_matrix, classes)
        self.fit = fit

    def evaluate_model(self, dataset, doi_docs=None, docid_to_mentions=None):
        """
        Returns performance metrics for the learned model on the given dataset

        :returns: a dictionary, mapping each scoring method to its value (precision, recall, f1)
        """
        if doi_docs is None:
            doi_docs = dataset.doi_docs

        nb_valid_predictions = 0
        nb_predictions = 0
        nb_item_judgments = 0

        for doc_id, doc in doi_docs:
            item_choices = dataset.get_item_choices((doc_id, doc))
            mentions = docid_to_mentions[(doc_id, doc)]
            self.classify_mentions(mentions)
            for mention in mentions:
                mention_id = (mention['start'], mention['end'])
                if mention_id in item_choices:
                    target_item = item_choices[mention_id]
                    if target_item is not None and target_item == mention['best_qid']:
                        nb_valid_predictions += 1
                    if mention['best_qid'] is not None:
                        nb_predictions += 1
                    if target_item is not None:
                        nb_item_judgments += 1
                    
        precision = float(nb_valid_predictions) / nb_predictions if nb_predictions else 1.
        recall = float(nb_valid_predictions) / nb_item_judgments if nb_item_judgments else 1
        f1 = 2*(precision*recall) / (precision + recall) if precision + recall > 0. else 0.
        return {
                'precision':precision,
                'recall':recall,
                'f1':f1
                }

    def build_feature_vectors_for_doc(self, mentions):
        """
        Given a list of mentions, create the matrix
        of input vectors for each of the tags in these
        mentions, with a dict mapping tag ids to row
        indices
        """
        # Build matrix of raw feature vectors
        all_feature_vectors = {}
        for mention in mentions:
            all_feature_vectors.update(self.feature_vectors_from_mention(mention))

        if not all_feature_vectors:
            return [], {}

        feature_array = []

        tag_key_to_idx = {}
        for mention in mentions:
            for tag in mention['tags']:
                tag_key = (mention['start'], mention['end'], tag['id'])
                tag_key_to_idx[tag_key] = len(feature_array)
                feature_array.append(all_feature_vectors[tag_key])

        feature_array = numpy.array(feature_array)

        # Build graph adjacency matrix
        adj_matrix = numpy.zeros(shape=(len(feature_array),len(feature_array)))
        for mention in mentions:
            for tag in mention['tags']:
                tag_idx = tag_key_to_idx[(mention['start'],mention['end'],tag['id'])]
                for similarity in tag['similarities']:
                    if not similarity['tag'] in tag_key_to_idx:
                        continue # the tag was pruned
                    other_tag_idx = tag_key_to_idx[similarity['tag']]
                    adj_matrix[other_tag_idx,tag_idx] = similarity['score']

        if self.mode == 'markov':
            transition_matrix = (1 - self.alpha) * adj_matrix + self.alpha*numpy.eye(len(feature_array))
            for i in range(self.nb_steps):
                feature_array = numpy.dot(transition_matrix, feature_array)
        elif self.mode == "restarts":
            for i in range(self.nb_steps):
                feature_array = self.alpha * feature_array + (1 - self.alpha) * numpy.dot(adj_matrix, feature_array)
        return feature_array, tag_key_to_idx

    def classify_mentions(self, mentions):
        """
        Given a list of mentions for a document,
        run the classifier on them and annotate
        them with their scores and decisions
        """
        feature_array, tag_key_to_idx = self.build_feature_vectors_for_doc(mentions)

        if tag_key_to_idx:
            predicted_classes = self.fit.decision_function(feature_array)

        for mention in mentions:
            start = mention['start']
            end = mention['end']
            max_score = 0
            best_tag = None
            for tag in mention['tags']:
                tag_key = (start, end, tag['id'])
                tag['score'] = predicted_classes[tag_key_to_idx[tag_key]]
                if tag['score'] > max_score:
                    max_score = tag['score']
                    best_tag = tag['id']
            mention['best_qid'] = best_tag


