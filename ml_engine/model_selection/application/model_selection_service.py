from ml_engine.model_selection.model_selection_engine import (ModelSelectionEngine)
from ml_engine.model_selection.preference_service import (PreferenceService)
from ml_engine.model_selection.preference_normalizer import (PreferenceNormalizer)

class ModelSelectionService:

    def __init__(self):

        self.model_selection_engine = (ModelSelectionEngine())
        self.preference_service = (PreferenceService())
        self.preference_normalizer = (PreferenceNormalizer())


    def select(self,context,user_preferences,algorithms):

        mapped_preferences = (
            self.preference_service
            .map_preferences(
                user_preferences
            )
        )

        normalized_preferences = (
            self.preference_normalizer
            .normalize(
                mapped_preferences
            )
        )

        results = (
            self.model_selection_engine
            .select_models(
                context,
                normalized_preferences,
                algorithms
            )
        )

        return results