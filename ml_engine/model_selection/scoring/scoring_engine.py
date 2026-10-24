from ml_engine.model_selection.algorithm_registry import eligibility
from ml_engine.model_selection.scoring.algorithm_scorer import AlgorithmScorer


class ScoringEngine:


    def __init__(self):
        self.scorer = AlgorithmScorer()

    def rank_algorithms(self, algorithms, preferences, dataset_features, problem_type=None, rows=0,
                        raw_preferences=None):
        ranked, excluded = [], []
        order = list(algorithms)

        for name, info in algorithms.items():
            reason = eligibility(name, problem_type or info.get("type"), rows, raw_preferences) if problem_type else None
            if reason:
                excluded.append({"algorithm": name, "reason": reason})
                continue
            ranked.append(self.scorer.score(name, info, preferences, dataset_features))

        ranked.sort(key=lambda r: (-r.score, order.index(r.algorithm_name)))
        self.excluded = excluded
        return ranked
