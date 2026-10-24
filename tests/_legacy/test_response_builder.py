from ml_engine.response.response_builder import (ResponseBuilder)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.model_selection.scoring.score_result import (AlgorithmScoreResult)

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

builder = ResponseBuilder()
response = builder.build(results,CLASSIFICATION_ALGORITHMS)

for item in response:

    print(item)