from ml_engine.model_selection.scoring.algorithm_scorer import (AlgorithmScorer)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)

scorer = AlgorithmScorer()
preferences = {
    "high_accuracy": True,
    "handles_noise": True
}

dataset_features = {
    "mixed_features": True,
    "numeric_features": True
}

result = scorer.score(

    "Random Forest",

    CLASSIFICATION_ALGORITHMS["Random Forest"],

    preferences,

    dataset_features)

print(result)