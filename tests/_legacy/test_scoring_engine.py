from ml_engine.model_selection.scoring.scoring_engine import (ScoringEngine)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)

engine = ScoringEngine()
preferences = {
    "high_accuracy": True,
    "handles_noise": True
}
dataset_features = {
    "mixed_features": True,
    "numeric_features": True
}
results = engine.rank_algorithms(

    CLASSIFICATION_ALGORITHMS,

    preferences,

    dataset_features
)

for result in results:
    print(result)