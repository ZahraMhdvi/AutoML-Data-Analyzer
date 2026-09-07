from ml_engine.model_selection.context_feature_extractor import (ContextFeatureExtractor)
from ml_engine.model_selection.scoring.scoring_engine import (ScoringEngine)


class ModelSelectionEngine:

    def __init__(self):
        self.feature_extractor = ContextFeatureExtractor()
        self.scoring_engine = ScoringEngine()


    def select_models(self,context,preferences,algorithms):
        dataset_features = (self.feature_extractor.extract(context))
        ranked_algorithms = (self.scoring_engine.rank_algorithms(algorithms,preferences,dataset_features))

        return ranked_algorithms