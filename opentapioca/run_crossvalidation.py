
if __name__ == '__main__':
    import sys
    from .wikidatagraph import WikidataGraph
    from .languagemodel import BOWLanguageModel
    from .tagger import Tagger
    from .goldstandard import GoldStandardDataset
    from .classifier import SimpleTagClassifier
    bow = BOWLanguageModel()
    bow.load(sys.argv[1])
    graph = WikidataGraph()
    graph.load_pagerank(sys.argv[2])
    tagger = Tagger(bow, graph)
    d = GoldStandardDataset(sys.argv[3])
    clf = SimpleTagClassifier(tagger)

    parameter_grid = []
    for mode in ['markov', 'restarts']:
        for nb_steps in [1, 2, 4, 8, 16, 32]:
            for C in [10.0, 1.0, 0.1, 0.01, 0.001, 0.0001]:
                for alpha in [0.1, 0.3, 0.4, 0.6, 0.8, 0.85, 0.9, 0.95]:
                    parameter_grid.append({
                        'nb_steps':nb_steps,
                        'alpha':alpha,
                        'C': C,
                        'mode': mode,
                        })

    best_params = clf.crossfit_model(d, parameter_grid)
    print('#########')
    print(best_params)
    clf.save('data/simple-classifier.pkl')

