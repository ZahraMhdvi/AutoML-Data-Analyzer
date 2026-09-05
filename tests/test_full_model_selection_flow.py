from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)
from ml_engine.model_selection.user_response_handler import (UserResponseHandler)
from ml_engine.model_selection.preference_mapper import (map_classification_preferences)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.model_selection.dataset_feature_analyzer import (DatasetFeatureAnalyzer)


FILE_PATH = "data/customer_dataset.xlsx"

analyzer = DatasetAnalyzer()
analysis_result = analyzer.analyze(FILE_PATH)

print("\nSTEP 1 RESULT")
print(analysis_result)


pipeline = PreprocessingPipeline(

    analysis_result["dataframe"],

    "classification",

    "Churn"

)


processed_result = pipeline.process()
clean_dataframe = processed_result["dataframe"]
target = processed_result["target"]
print("\nSTEP 2 RESULT")
print(clean_dataframe.shape)


answers = {

    "main_goal": "accuracy",

    "data_growth": "static_data",

    "feature_dimension": "normal_dimension",

    "noise_presence": "has_noise"
}
handler = UserResponseHandler()
preferences = handler.create_preferences(answers)
mapped_preferences = map_classification_preferences(preferences)

print("\nUSER PREFERENCES")
print(mapped_preferences)


builder = ModelSelectionContextBuilder()
context = builder.build(
    analysis_result,
    clean_dataframe,
    mapped_preferences,
    "classification"
)


print("\nCONTEXT")
print(context)

feature_analyzer = DatasetFeatureAnalyzer()
dataset_features = feature_analyzer.analyze(context)



print("\nDATASET FEATURES")
print(dataset_features)