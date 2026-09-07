from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)
from ml_engine.problem_selection.problem_choice_handler import (ProblemChoiceHandler)
from ml_engine.model_selection.question_service import (QuestionService)
from ml_engine.model_selection.user_answer_handler import (UserAnswerHandler)
from ml_engine.model_selection.preference_service import (PreferenceService)
from ml_engine.model_selection.preference_normalizer import (PreferenceNormalizer)
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.model_selection.model_selection_engine import (ModelSelectionEngine)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)


FILE_PATH = "data/customer_dataset.xlsx"

analysis_result = DatasetAnalyzer().analyze(FILE_PATH)

print("\nSTEP 1")

recommendations = (
    ProblemRecommendationEngine()
    .recommend(
        analysis_result
    )
)

print("\nSTEP 2")
print(recommendations)

selected_problem = (
    ProblemChoiceHandler()
    .choose(
        recommendations,
        "classification"
    )
)


print("\nSELECTED PROBLEM")
print(selected_problem)


questions = (
    QuestionService()
    .get_questions(
        selected_problem
    )
)

print("\nQUESTIONS")
print(len(questions))

answers = {

    "main_goal":
        "accuracy",

    "data_growth":
        "static_data",

    "feature_dimension":
        "normal_dimension",

    "noise_presence":
        "has_noise"
}


preferences = (
    UserAnswerHandler()
    .create_preferences(

        answers,
        selected_problem
    )
)


print("\nUSER PREFERENCES")
print(preferences)


mapped_preferences = (
    PreferenceService()
    .map_preferences(
        preferences
    )
)


normalized_preferences = (
    PreferenceNormalizer()
    .normalize(
        mapped_preferences
    )
)


print("\nNORMALIZED")
print(normalized_preferences)

processed = (PreprocessingPipeline(analysis_result["dataframe"],selected_problem,"Churn").process())


context = (
    ModelSelectionContextBuilder()
    .build(

        analysis_result,
        processed["dataframe"],
        normalized_preferences,
        selected_problem
    )
)



results = (
    ModelSelectionEngine()
    .select_models(

        context,
        normalized_preferences,
        CLASSIFICATION_ALGORITHMS
    )
)

print("\nFINAL RANKING")
for result in results:

    print(result)