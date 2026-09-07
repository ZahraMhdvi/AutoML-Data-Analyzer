from ml_engine.response.model_selection_response_builder import (ModelSelectionResponseBuilder)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.model_selection.scoring.score_result import (AlgorithmScoreResult)
from dataclasses import dataclass



@dataclass
class FakeContext:

    problem_type="classification"
    target="Churn"

results = [
    AlgorithmScoreResult(
        algorithm_name="Random Forest",
        score=70,
        matched=[
            "high_accuracy",
            "handles_noise",
            "mixed_features"
        ],
        unmatched=[]
    )

]

response = (ModelSelectionResponseBuilder().build(FakeContext(),results,
        CLASSIFICATION_ALGORITHMS
    )
)

print(response)