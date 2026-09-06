from ml_engine.model_selection.preference_normalizer import (PreferenceNormalizer)

normalizer = PreferenceNormalizer()

preferences = {

    "preferred_accuracy": True,

    "preferred_speed": False,

    "preferred_interpretability": False,

    "needs_noise_handling": True,

    "needs_high_dimension_support": False

}

result = normalizer.normalize(preferences)
print(result)