from dataclasses import asdict

from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.model_selection.preference_schema import UserPreferences
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.model_selection.model_selection_engine import (ModelSelectionEngine)
from ml_engine.response.model_selection_response_builder import (ModelSelectionResponseBuilder)
from ml_engine.model_selection.preference_service import (PreferenceService)
from ml_engine.model_selection.preference_normalizer import (PreferenceNormalizer)
from ml_engine.model_selection.data_characteristics import (DataCharacteristicsDetector)


class ModelSelectionApplication:


    def __init__(self):
        self.analyzer = DatasetAnalyzer()
        self.context_builder = (ModelSelectionContextBuilder())
        self.engine = (ModelSelectionEngine())
        self.response_builder = (ModelSelectionResponseBuilder())
        self.preference_service = (PreferenceService())
        self.preference_normalizer = (PreferenceNormalizer())
        self.characteristics_detector = (DataCharacteristicsDetector())

    def run(
            self,
            file_path,
            problem_type,
            target,
            user_preferences,
            algorithms,
            generated_dataset_id=None
    ):


        if generated_dataset_id:

            from api.routes.ai_target import generated_datasets

            if generated_dataset_id not in generated_datasets:
                raise ValueError(
                    "Generated dataset not found"
                )

            dataframe = generated_datasets[
                generated_dataset_id
            ]

        else:

            dataframe = self.analyzer.loader.load_excel(file_path)

        return self.run_dataframe(
            dataframe,
            problem_type,
            target,
            user_preferences,
            algorithms
        )

    def run_dataframe(
            self,
            dataframe,
            problem_type,
            target,
            user_preferences,
            algorithms
    ):

        if problem_type == "clustering":
            target = None

        analysis_result = self.analyzer.analyze_dataframe(dataframe)

        processed = (
            PreprocessingPipeline(
                analysis_result["dataframe"],
                problem_type,
                target
            ).process()
        )


        characteristics = self.characteristics_detector.detect(
            dataframe,
            target=target,
            encoded_feature_count=processed["dataframe"].shape[1]
        )

        if isinstance(user_preferences, UserPreferences):
            user_preferences = asdict(user_preferences)

        user_preferences = dict(user_preferences or {})

        user_preferences["noise_presence"] = characteristics["noise_presence"]

        if problem_type == "classification":
            user_preferences["feature_dimension"] = characteristics["feature_dimension"]

        preferences = UserPreferences(
            cluster_count=user_preferences.get(
                "cluster_count"
            ),
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
                preferences,
                problem_type
            )
        )

        context.target = target

        mapped_preferences = (
            self.preference_service
            .map_preferences(
                preferences
            )
        )

        normalized_preferences = (self.preference_normalizer.normalize(mapped_preferences))

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

        response.data_characteristics = characteristics

        return response
