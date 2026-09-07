from ml_engine.explanation.explanation_engine import (ExplanationEngine)
from ml_engine.model_selection.algorithm_registry import CLASSIFICATION_ALGORITHMS
from ml_engine.model_selection.scoring.score_result import (AlgorithmScoreResult)

result = AlgorithmScoreResult(
    algorithm_name="Random Forest",
    score=70,
    matched=[
        "high_accuracy",
        "handles_noise",
        "mixed_features"
    ],
    unmatched=[]
)

engine = ExplanationEngine()
explanation = engine.generate(result)
print(explanation)

print(  CLASSIFICATION_ALGORITHMS["Random Forest"])