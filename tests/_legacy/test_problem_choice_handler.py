from ml_engine.problem_selection.problem_choice_handler import (
    ProblemChoiceHandler)

from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)

from ml_engine.analyzer_service import DatasetAnalyzer



FILE_PATH = "data/customer_dataset.xlsx"
analysis_result = DatasetAnalyzer().analyze(FILE_PATH)
recommendations = ProblemRecommendationEngine().recommend(analysis_result)
handler = ProblemChoiceHandler()

selected = handler.choose(
    recommendations,
"clustering"
)

print(selected)