from ml_engine.model_selection.scoring.capability_matcher import (CapabilityMatcher)

matcher = CapabilityMatcher()
preferences = {
    "high_accuracy": True,
    "handles_noise": True,
    "fast": False
}

result = matcher.expand_preferences(preferences)
print(result)