import logging
import pickle
from collections import defaultdict

import numpy
from sklearn import preprocessing, svm
from sklearn.pipeline import Pipeline

from .similarities import DirectLinkSimilarity, EdgeRatioSimilarity, OneStepSimilarity

logger = logging.getLogger(__name__)


class SimpleTagClassifier(object):
    """
    A linear support vector classifier to predict the validity of a tag in a mention.
    """

    def __init__(
        self,
        tagger,
        beta=0.85,
        nb_steps=2,
        C=0.001,
        max_similarity_distance=100,
        similarity_smoothing=0.1,
        similarity="direct_link",
    ):
        self.tagger = tagger
        self.beta = beta
        self.nb_steps = nb_steps
        self.C = C
        self.identifier_space = "http://www.wikidata.org/entity/"
        self.similarity = similarity
        self.max_similarity_distance = max_similarity_distance
        if similarity == "direct_link":
            self.similarity_method = DirectLinkSimilarity()
        elif similarity == "edge_ratio":
            self.similarity_method = EdgeRatioSimilarity()
        else:
            self.similarity_method = OneStepSimilarity(beta)
        self.similarity_smoothing = similarity_smoothing

    def feature_vectors_from_mention(self, mention):
        """
        Returns a dictionary of tag keys to feature vectors
        in a mention
        """
        dct = {}
        for tag in mention.tags:
            feature_vector = [
                mention.log_likelihood,
                tag.rank,
                tag.nb_statements,
                tag.nb_sitelinks,
                1,
            ]
            tag_key = mention.tag_key(tag.id)
            dct[tag_key] = feature_vector
        return dct

    def load(self, fname):
        """
        Loads the classifier from a file (.pkl format).
        The tagger must be restored manually afterwards.
        """
        with open(fname, "rb") as f:
            dct = pickle.load(f)
        if "tagger" in dct:
            del dct["tagger"]
        self.__dict__.update(dct)

    def save(self, fname):
        """
        Saves the classifier to a file (.pkl format).
        """
        with open(fname, "wb") as f:
            dct = dict(self.__dict__.items())
            del dct["tagger"]
            pickle.dump(dct, f)

    def create_mentions(self, phrase):
        """
        Runs the Solr tagger to create the mentions
        and compute the similarities between them.
        """
        mentions = self.tagger.tag_and_rank(phrase)
        for mention in mentions:
            self.compute_similarities(mention, mentions)
        return mentions

    def tag_dataset(self, dataset):
        """
        Runs the tagger on the entire dataset and
        returns a map docid -> mentions
        """
        docid_to_mentions = {}
        for context in dataset.contexts:
            docid = str(context.uri)
            docid_to_mentions[docid] = self.create_mentions(context.mention)
        return docid_to_mentions

    def crossfit_model(self, dataset, parameters=None, max_iter=100):
        """
        Learns the model and report F1 score
        with cross-validation.
        """
        k = 5
        chunks = [set() for i in range(k)]
        for idx, context in enumerate(dataset.contexts):
            chunks[idx % k].add(context)
        logger.info("Chunk lengths:")
        logger.info([len(chunk) for chunk in chunks])

        all_contexts = set(dataset.contexts)

        # tag all documents once and for all
        docid_to_mentions = {}
        for idx, context in enumerate(all_contexts):
            if idx % 100 == 0:
                logger.info("{}...".format(idx))
            docid_to_mentions[str(context.uri)] = self.create_mentions(context.mention)

        if parameters is None:
            parameters = [{}]

        best_params = {}
        best_f1 = 0.0
        best_classifier = None
        for idx, param_setting in enumerate(parameters):
            # Set the parameters
            for param, val in param_setting.items():
                setattr(self, param, val)

            # Recompute similarities
            for uri, mentions in docid_to_mentions.items():
                for mention in mentions:
                    self.compute_similarities(mention, mentions)

            # Run cross-validation
            scores = defaultdict(float)
            for chunk_id in range(k):
                training_chunks = all_contexts - chunks[chunk_id]
                self.train_model(dataset, training_chunks, docid_to_mentions)
                chunk_scores = self.evaluate_model(chunks[chunk_id], docid_to_mentions)
                for method, score in chunk_scores.items():
                    scores[method] += score / k
            logger.info("----- {}/{}".format(idx, len(parameters)))
            logger.info(param_setting)
            logger.info(dict(scores.items()))
            if scores["f1"] > best_f1:
                print("(best so far)")
                best_params = param_setting
                best_f1 = scores["f1"]
                # Retrain on whole dev set with these parameters
                self.train_model(dataset, None, docid_to_mentions, max_iter=max_iter)
                best_classifier = self.fit
                self.save("data/best_classifier_so_far.pkl")
            else:
                self.save("data/latest_classifier.pkl")

        self.fit = best_classifier
        return best_params, best_f1

    def train_model(self, dataset, docids=None, docid_to_mentions=None, max_iter=100):
        """
        Train the model on the given NIF dataset, restricting the training
        to the given document identifiers.

        :param docid_to_mentions: a map from document ids to pre-computed
            mentions, to avoid re-tagging the dataset multiple times if training
            is running multiple times.
        """
        docid_to_mentions = docid_to_mentions or {}

        design_matrix = []
        classes = []
        nb_valid = 0
        for context in dataset.contexts:

            # Obtain all the suggested mentions from the tagger (or the cache)
            mentions = docid_to_mentions.get(str(context.uri))
            if mentions is None:
                mentions = self.tagger.tag_and_rank(context.mention)

            # Build the feature vectors for these mentions
            feature_vectors, tag_indices = self.build_feature_vectors_for_doc(mentions)

            # Match the phrases in the dataset to mentions and mark them as valid
            mention_index = {mention.key(): mention for mention in mentions}
            for phrase in context.phrases:
                if not phrase.taIdentRef or not phrase.taIdentRef.startswith(
                    self.identifier_space
                ):
                    continue
                phrase_qid = phrase.taIdentRef[len(self.identifier_space) :]
                mention = mention_index.get((phrase.beginIndex, phrase.endIndex))
                if mention:
                    for tag in mention.tags:
                        tag.valid = tag.id == phrase_qid

            # Construct design matrix and class vector
            for mention in mentions:
                for tag in mention.tags:
                    tag_id = mention.tag_key(tag.id)
                    if tag_id in tag_indices:
                        design_matrix.append(feature_vectors[tag_indices[tag_id]])
                        validity = int(tag.valid or False)
                        classes.append(validity)
                        nb_valid += validity
                        # print('{}: {}'.format(str((tag_id)), validity))
                        # print(feature_vectors[tag_indices[tag_id]])

        # print('nb positive {}, total {}'.format(nb_valid, len(design_matrix)))
        if not nb_valid:
            print("No positive sample found, exiting")
            return

        scaler = preprocessing.StandardScaler()
        clf = svm.LinearSVC(class_weight="balanced", C=self.C, max_iter=max_iter)
        pipeline = Pipeline([("scaler", scaler), ("svm", clf)])

        fit = pipeline.fit(design_matrix, classes)
        self.fit = fit

    def evaluate_model(self, contexts, docid_to_mentions=None):
        """
        Returns performance metrics for the learned model on the given dataset

        :param ids: restricts the evaluation to the given context ids
        :returns: a dictionary, mapping each scoring method to its value (precision, recall, f1)
        """
        nb_valid_predictions = 0
        nb_predictions = 0
        nb_item_judgments = 0

        for context in contexts:
            context_id = str(context.uri)
            mention_id_to_qid = {
                (phrase.beginIndex, phrase.endIndex): phrase.taIdentRef[
                    len(self.identifier_space) :
                ]
                for phrase in context.phrases
                if phrase.taIdentRef
                and phrase.taIdentRef.startswith(self.identifier_space)
            }
            nb_item_judgments += len(mention_id_to_qid)
            mentions = docid_to_mentions[context_id]
            self.classify_mentions(mentions)
            for mention in mentions:
                mention_id = mention.key()
                target_item = mention_id_to_qid.get(mention_id)
                if target_item is not None and target_item == mention.best_qid:
                    nb_valid_predictions += 1
                if mention.best_qid is not None:
                    nb_predictions += 1
                if target_item is None and mention.best_qid is not None:
                    logger.debug(
                        "False positive: {} in context {}".format(mention, context)
                    )

        # print({'nb_valid_predictions':nb_valid_predictions, 'nb_predictions': nb_predictions, 'nb_item_judgments':nb_item_judgments})
        precision = (
            float(nb_valid_predictions) / nb_predictions if nb_predictions else 1.0
        )
        recall = (
            float(nb_valid_predictions) / nb_item_judgments if mention_id_to_qid else 1
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if precision + recall > 0.0
            else 0.0
        )
        return {"precision": precision, "recall": recall, "f1": f1}

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
            for tag in mention.tags:
                tag_key = mention.tag_key(tag.id)
                tag_key_to_idx[tag_key] = len(feature_array)
                feature_array.append(all_feature_vectors[tag_key])

        feature_array = numpy.array(feature_array)

        # Build graph adjacency matrix
        adj_matrix = numpy.zeros(shape=(len(feature_array), len(feature_array)))
        for mention in mentions:
            for tag in mention.tags:
                tag_idx = tag_key_to_idx[mention.tag_key(tag.id)]
                for similarity in tag.similarities:
                    if not similarity["tag"] in tag_key_to_idx:
                        continue  # the tag was pruned
                    other_tag_idx = tag_key_to_idx[similarity["tag"]]
                    adj_matrix[other_tag_idx, tag_idx] = similarity["score"]

        mixed_features = feature_array
        mixed_features_array = [feature_array]
        mixed_features = mixed_features.astype(float)

        for i in range(self.nb_steps):
            mixed_features = numpy.dot(adj_matrix, mixed_features)
            mixed_features_array.append(mixed_features)
        feature_array = numpy.hstack(mixed_features_array)

        return feature_array, tag_key_to_idx

    def classify_mentions(self, mentions):
        """
        Given a list of mentions for a document,
        run the classifier on them and annotate
        them with their scores and decisions
        """
        feature_array, tag_key_to_idx = self.build_feature_vectors_for_doc(mentions)

        logger.debug("Classifying mentions")
        if tag_key_to_idx:
            predicted_classes = self.fit.decision_function(feature_array)
        nb_tags = 0

        for mention in mentions:
            start = mention.start
            end = mention.end
            max_score = 0
            best_tag = None
            for tag in mention.tags:
                nb_tags += 1
                tag_key = (start, end, tag.id)
                tag.score = predicted_classes[tag_key_to_idx[tag_key]]
                if tag.score > max_score:
                    max_score = tag.score
                    best_tag = tag.id
            mention.best_qid = best_tag
        logger.debug("Mentions classified ({} tags)".format(nb_tags))

    def compute_similarities(self, mention, all_mentions):
        """
        Compute similarity on each tag of a mention, to other tags in the same document
        """
        start = mention.start
        end = mention.end
        for tag in mention.tags:
            similarities = [
                {"tag": mention.tag_key(tag.id), "score": self.similarity_smoothing}
            ]
            other_tag_ids = []
            for other_mention in all_mentions:
                other_start = other_mention.start
                other_end = other_mention.end
                distance = max(start - other_end, other_start - end)
                # distance = abs((other_end + other_start - end - start) / 2)
                if (
                    other_start == start and other_end == end
                ) or distance > self.max_similarity_distance:
                    continue
                for other_tag in other_mention.tags:
                    other_tag_id = other_mention.tag_key(other_tag.id)
                    similarity = (
                        self.similarity_smoothing
                        + self.similarity_method.compute_similarity(tag, other_tag)
                    )
                    similarity *= (
                        float(self.max_similarity_distance - distance)
                        / self.max_similarity_distance
                    )
                    other_tag_ids.append(other_tag_id)
                    if similarity > 0.0:
                        similarities.append({"tag": other_tag_id, "score": similarity})

            # Normalize
            weight_sum = sum(similarity["score"] for similarity in similarities)

            if weight_sum > 0.0:
                tag.similarities = [
                    {"tag": sim["tag"], "score": sim["score"] / weight_sum}
                    for sim in similarities
                ]
