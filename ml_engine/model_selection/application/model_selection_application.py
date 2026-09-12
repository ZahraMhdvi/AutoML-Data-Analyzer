from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.model_selection.preference_schema import UserPreferences
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.model_selection.model_selection_engine import (ModelSelectionEngine)
from ml_engine.response.model_selection_response_builder import (ModelSelectionResponseBuilder)
from ml_engine.model_selection.preference_service import (PreferenceService)
from ml_engine.model_selection.preference_normalizer import (PreferenceNormalizer)


class ModelSelectionApplication:


    def __init__(self):
        self.analyzer = DatasetAnalyzer()
        self.context_builder = (ModelSelectionContextBuilder())
        self.engine = (ModelSelectionEngine())
        self.response_builder = (ModelSelectionResponseBuilder())
        self.preference_service = (PreferenceService())
        self.preference_normalizer = (PreferenceNormalizer())


    def run(self,file_path,problem_type,target,user_preferences,algorithms):

        analysis_result = (self.analyzer.analyze(file_path))
        processed = (PreprocessingPipeline(analysis_result["dataframe"],problem_type,target).process())

        if isinstance(user_preferences, dict):
            user_preferences = UserPreferences(

                problem_type=problem_type,

                main_goal=user_preferences.get(
                    "main_goal"
                ),

                data_growth=user_preferences.get(
                    "data_growth"
                ),

                feature_dimension=user_preferences.get(
                    "feature_dimension"
                ),

                noise_presence=user_preferences.get(
                    "noise_presence"
                ),


                cluster_count_known=user_preferences.get(
                    "cluster_count_known"
                ),

                cluster_shape=user_preferences.get(
                    "cluster_shape"
                ),

                hierarchical_analysis=user_preferences.get(
                    "hierarchical_analysis"
                )

            )

            context = (
            self.context_builder.build(
                analysis_result,
                processed["dataframe"],
                user_preferences,
                problem_type

            )
        )
        mapped_preferences = (
            self.preference_service
            .map_preferences(
                user_preferences
            )
        )
        print(
            "RAW USER PREF:",
            user_preferences
        )

        print(
            "MAPPED PREF:",
            mapped_preferences
        )

        normalized_preferences = (self.preference_normalizer.normalize(mapped_preferences))
        print(
            "NORMALIZED PREF:",
            normalized_preferences
        )
        ranking = (
            self.engine.select_models(
                context,
                normalized_preferences,
                algorithms
            )
        )
        ranking = sorted(

            ranking,

            key=lambda x: x.score,

            reverse=True

        )


        response = (
            self.response_builder.build(
                context,
                ranking,
                algorithms
            )
        )


        return response