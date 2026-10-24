from ml_engine.model_selection.context_feature_extractor import ContextFeatureExtractor
from ml_engine.model_selection.scoring.scoring_engine import ScoringEngine


class ModelSelectionEngine:

    def __init__(self):
        self.feature_extractor = ContextFeatureExtractor()
        self.scoring_engine = ScoringEngine()
        self.excluded = []
        self.dataset_features = {}

    def select_models(self, context, preferences, algorithms, raw_preferences=None):
        self.dataset_features = self.feature_extractor.extract(context)
        ranked = self.scoring_engine.rank_algorithms(
            algorithms, preferences, self.dataset_features,
            problem_type=context.problem_type, rows=context.clean_data_shape["rows"],
            raw_preferences=raw_preferences,
        )
        self.excluded = self.scoring_engine.excluded
        return ranked
