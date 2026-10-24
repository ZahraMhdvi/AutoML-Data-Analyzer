from dataclasses import asdict

from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.model_selection.context_builder import ModelSelectionContextBuilder
from ml_engine.model_selection.data_characteristics import DataCharacteristicsDetector
from ml_engine.model_selection.model_selection_engine import ModelSelectionEngine
from ml_engine.model_selection.preference_normalizer import PreferenceNormalizer
from ml_engine.model_selection.preference_schema import UserPreferences
from ml_engine.model_selection.preference_service import PreferenceService
from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.response.model_selection_response_builder import ModelSelectionResponseBuilder


PREFERENCE_FIELDS = ("cluster_count", "main_goal", "data_growth", "feature_dimension", "noise_presence",
                     "cluster_count_known", "cluster_shape", "hierarchical_analysis")


class ModelSelectionApplication:


    def __init__(self):
        self.analyzer = DatasetAnalyzer()
        self.context_builder = ModelSelectionContextBuilder()
        self.engine = ModelSelectionEngine()
        self.response_builder = ModelSelectionResponseBuilder()
        self.preference_service = PreferenceService()
        self.preference_normalizer = PreferenceNormalizer()
        self.characteristics_detector = DataCharacteristicsDetector()

    def run_dataframe(self, dataframe, problem_type, target, user_preferences, algorithms):
        if problem_type == "clustering":
            target = None

        analysis_result = self.analyzer.analyze_dataframe(dataframe)


        features_frame = dataframe.drop(columns=[target]) if target and target in dataframe.columns else dataframe
        encoded = PreprocessingPipeline(problem_type=problem_type).fit(features_frame).transform(features_frame.head(1))

        characteristics = self.characteristics_detector.detect(
            dataframe, target=target, encoded_feature_count=encoded.shape[1])

        if isinstance(user_preferences, UserPreferences):
            user_preferences = asdict(user_preferences)
        user_preferences = dict(user_preferences or {})
        user_preferences["noise_presence"] = characteristics["noise_presence"]
        if problem_type == "classification":
            user_preferences["feature_dimension"] = characteristics["feature_dimension"]

        preferences = UserPreferences(problem_type=problem_type,
                                      **{key: user_preferences.get(key) for key in PREFERENCE_FIELDS})

        context = self.context_builder.build(analysis_result, encoded, preferences, problem_type)
        context.clean_data_shape["rows"] = int(len(dataframe))
        context.target = target

        mapped = self.preference_normalizer.normalize(self.preference_service.map_preferences(preferences))
        ranking = self.engine.select_models(context, mapped, algorithms, raw_preferences=user_preferences)

        response = self.response_builder.build(
            context, ranking, algorithms, excluded=self.engine.excluded,
            dataset_features=self.engine.dataset_features)
        response.data_characteristics = characteristics
        return response
