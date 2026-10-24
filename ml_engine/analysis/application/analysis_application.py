from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.problem_selection.problem_recommendation_engine import (ProblemRecommendationEngine)


class AnalysisApplication:

    def __init__(self):

        self.analyzer = DatasetAnalyzer()
        self.problem_engine = ProblemRecommendationEngine()


    def analyze(self, file_path):

        analysis_result = self.analyzer.analyze(file_path)

        return self._build(analysis_result)

    def analyze_dataframe(self, dataframe):

        analysis_result = self.analyzer.analyze_dataframe(dataframe)

        return self._build(analysis_result)

    def _build(self, analysis_result):
        recommendations = (self.problem_engine.recommend(analysis_result))
        recommended_targets = [
            target
            for target in analysis_result["targets"]
            if target["score"] >= 80
        ]

        possible_targets = [
            target
            for target in analysis_result["targets"]
            if 50 <= target["score"] < 80
        ]
        available_targets = (
                recommended_targets
                +
                possible_targets
        )
        from dataclasses import asdict
        from ml_engine.validation import validate_dataframe, column_kinds

        dataframe = analysis_result["dataframe"]

        return {

            "profile": analysis_result["profile"],
            "issues": validate_dataframe(dataframe),
            "column_kinds": column_kinds(dataframe),
            "problem_recommendations": {key: asdict(value) for key, value in recommendations.items()},
            "recommended_targets": recommended_targets,
            "possible_targets": possible_targets,
            "target_required":
                len(recommended_targets) == 0 and len(possible_targets) == 0,
            "available_targets": available_targets,
            "manual_targets":
                analysis_result["manual_targets"],

        }