from ml_engine.model_selection.scoring.algorithm_scorer import (
    AlgorithmScorer
)


class ScoringEngine:


    def __init__(self):
        self.scorer = AlgorithmScorer()

    def rank_algorithms(
            self,
            algorithms,
            preferences,
            dataset_features
    ):

        results = []
        for algorithm_name, algorithm_info in algorithms.items():
            result = self.scorer.score(
                algorithm_name,
                algorithm_info,
                preferences,
                dataset_features
            )

            results.append(result)

        results.sort(key=lambda x: x.score,reverse=True)

        return results