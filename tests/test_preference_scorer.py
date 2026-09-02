from ml_engine.model_selection.preference_scorer import (PreferenceScorer)


algorithm = {
    "strengths":[
        "high_accuracy",
        "handles_noise"
    ]
}

preferences = {
    "high_accuracy": True,
    "handles_noise": True,
    "fast": False
}

scorer = PreferenceScorer()
result = scorer.score(algorithm,preferences,"classification")
print(result)