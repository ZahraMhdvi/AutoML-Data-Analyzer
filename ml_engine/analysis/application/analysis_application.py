from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)


class AnalysisApplication:

    def __init__(self):

        self.analyzer = DatasetAnalyzer()
        self.problem_engine = ProblemRecommendationEngine()


    def analyze(self, file_path):

        analysis_result = self.analyzer.analyze(file_path)
        recommendations = (self.problem_engine.recommend(analysis_result))
        recommended_targets = [
            target
            for target in analysis_result["targets"]
            if target["score"] >= 80
        ]

        possible_targets = [
            target
            for target in analysis_result["targets"]
            if target["score"] < 80
        ]
        return {

            "profile": analysis_result["profile"],
            "problem_recommendations": recommendations,
            "recommended_targets": recommended_targets,
            "possible_targets": possible_targets,
            "target_required": len(recommended_targets) == 0

        }