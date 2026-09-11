from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)


class AnalysisApplication:

    def __init__(self):

        self.analyzer = DatasetAnalyzer()
        self.problem_engine = ProblemRecommendationEngine()


    def analyze(self, file_path):

        analysis_result = self.analyzer.analyze(file_path)
        recommendations = (self.problem_engine.recommend(analysis_result))

        return {

            "profile": analysis_result["profile"],
            "problem_recommendations": recommendations,
            "target_candidates": analysis_result["targets"]
        }