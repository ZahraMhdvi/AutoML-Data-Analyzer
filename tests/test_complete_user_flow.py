from ml_engine.analyzer_service import DatasetAnalyzer


from ml_engine.problem_selection.problem_recommendation_engine import (
    ProblemRecommendationEngine
)


from ml_engine.problem_selection.problem_choice_handler import (
    ProblemChoiceHandler
)


from ml_engine.preprocessing.pipeline import (
    PreprocessingPipeline
)


from ml_engine.model_selection.user_response_handler import (
    UserResponseHandler
)


from ml_engine.model_selection.preference_mapper import (
    map_classification_preferences
)


from ml_engine.model_selection.context_builder import (
    ModelSelectionContextBuilder
)



FILE_PATH = "data/customer_dataset.xlsx"

analyzer = DatasetAnalyzer()
analysis_result = analyzer.analyze(FILE_PATH)

print("\nANALYSIS DONE")

recommendation_engine = ProblemRecommendationEngine()
recommendations = recommendation_engine.recommend( analysis_result)
print("\nPROBLEM RECOMMENDATIONS")
print(recommendations)
choice_handler = ProblemChoiceHandler()
selected_problem = choice_handler.choose(recommendations,"classification")

print("\nUSER SELECTED")
print(selected_problem)
pipeline = PreprocessingPipeline(
    analysis_result["dataframe"],
    selected_problem,
    analysis_result["targets"][0]["column"]

)


processed_result = pipeline.process()
clean_dataframe = processed_result["dataframe"]
print("\nPREPROCESSING DONE")
print(clean_dataframe.shape)
answers = {

    "main_goal": "accuracy",

    "data_growth": "static_data",

    "feature_dimension": "normal_dimension",

    "noise_presence": "has_noise"

}



handler = UserResponseHandler()
preferences = handler.create_preferences(answers)
preferences.problem_type = selected_problem

mapped_preferences = map_classification_preferences(preferences)
print("\nPREFERENCES")
print(mapped_preferences)
builder = ModelSelectionContextBuilder()
context = builder.build(

    analysis_result,

    clean_dataframe,

    mapped_preferences,

    selected_problem

)

print("\nFINAL CONTEXT")
print(context)