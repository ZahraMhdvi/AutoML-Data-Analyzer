import itertools

import numpy as np
import pandas as pd

from ml_engine.analysis.application.analysis_application import AnalysisApplication
from ml_engine.model_selection.algorithm_registry import CLASSIFICATION_ALGORITHMS, CLUSTERING_ALGORITHMS, eligibility
from ml_engine.model_selection.scoring.algorithm_scorer import AlgorithmScorer
from ml_engine.model_selection.scoring.scoring_engine import ScoringEngine


PREFS = ["high_accuracy", "fast", "interpretable", "handles_noise", "high_dimension", "large_dataset"]
DATA = ["small_dataset", "large_dataset", "high_dimension", "numeric_features", "categorical_features",
        "mixed_features"]


def test_compatibility_score_is_bounded_for_every_evidence_combination():
    scorer = AlgorithmScorer()
    for r in range(len(PREFS) + 1):
        for prefs in itertools.combinations(PREFS, r):
            for data in ([], DATA[:2], DATA):
                for name, info in {**CLASSIFICATION_ALGORITHMS, **CLUSTERING_ALGORITHMS}.items():
                    result = scorer.score(name, info, {p: True for p in prefs}, {d: True for d in data})
                    assert 0.0 <= result.score <= 100.0
                    assert abs(result.raw) <= result.bound or result.bound == 0


def test_no_evidence_gives_neutral_score():
    result = AlgorithmScorer().score("KNN", CLASSIFICATION_ALGORITHMS["KNN"], {}, {})
    assert result.score == 50.0


def test_rationale_contains_codes_and_points():
    result = AlgorithmScorer().score("Random Forest", CLASSIFICATION_ALGORITHMS["Random Forest"],
                                     {"high_accuracy": True}, {"mixed_features": True})
    codes = {(r["code"], r["source"], r["points"]) for r in result.reasons}
    assert ("high_accuracy", "preference", 40.0) in codes and ("mixed_features", "data", 10.0) in codes


def test_ineligible_algorithms_are_filtered_not_scored():
    engine = ScoringEngine()
    ranked = engine.rank_algorithms(CLASSIFICATION_ALGORITHMS, {}, {}, problem_type="classification", rows=30000)
    assert "SVM" not in [r.algorithm_name for r in ranked]
    assert {"algorithm": "SVM", "reason": "SVM_TOO_MANY_ROWS"} in engine.excluded

    ranked = engine.rank_algorithms(CLUSTERING_ALGORITHMS, {}, {}, problem_type="clustering", rows=100,
                                    raw_preferences={"cluster_count_known": True})
    assert "DBSCAN" not in [r.algorithm_name for r in ranked]
    assert eligibility("KMeans", "clustering", 10**6) is None


def _analysis(df):
    return AnalysisApplication().analyze_dataframe(df)["problem_recommendations"]


def test_problem_recommendation_statuses_are_deterministic():
    rng = np.random.default_rng(0)
    labelled = pd.DataFrame({"a": rng.normal(size=100), "b": rng.normal(size=100),
                             "churn": rng.choice(["yes", "no"], 100)})
    rec = _analysis(labelled)
    assert rec["classification"]["status"] == "recommended"
    assert rec["clustering"]["status"] == "potentially_suitable"
    assert "TARGET_EXISTS_CLASSIFICATION_LIKELY" in [e["code"] for e in rec["clustering"]["evidence"]]

    unlabelled = labelled.drop(columns=["churn"])
    rec = _analysis(unlabelled)
    assert rec["clustering"]["status"] == "recommended"
    assert rec["classification"]["status"] == "potentially_suitable"

    tiny = labelled.iloc[:6]
    rec = _analysis(tiny)
    assert rec["classification"]["status"] == "not_suitable"
    assert rec["clustering"]["status"] == "not_suitable"
    assert "score" not in rec["classification"]
