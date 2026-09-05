from ml_engine.analyzer_service import DatasetAnalyzer

from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)


FILE_PATH = "data/customer_dataset.xlsx"
analyzer = DatasetAnalyzer()
analysis_result = analyzer.analyze(FILE_PATH)
engine = ProblemRecommendationEngine()
result = engine.recommend(analysis_result)
print(result)