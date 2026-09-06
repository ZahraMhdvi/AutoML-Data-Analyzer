from ml_engine.model_selection.preference_mapper import (
    map_classification_preferences,
    map_clustering_preferences
)



class PreferenceService:

    def map_preferences(self,preferences):

        if preferences.problem_type == "classification":
            return map_classification_preferences(preferences)

        elif preferences.problem_type == "clustering":
            return map_clustering_preferences(preferences)

        else:

            raise ValueError(
                "Unsupported problem type"
            )