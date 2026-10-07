from ml_engine.problem_selection.problem_report import (
    ProblemRecommendation
)



class ProblemRecommendationEngine:



    def recommend(self, analysis_result):


        classification = self._analyze_classification(analysis_result)
        clustering = self._analyze_clustering(analysis_result)
        recommendations = [classification,clustering]

        recommendations.sort(key=lambda x: x.score,reverse=True)
        for index, recommendation in enumerate(recommendations,start=1):
            recommendation.priority = index

        return {

            "classification": classification,
            "clustering": clustering

        }



    def _analyze_classification(self,analysis_result):
        eligibility = analysis_result["eligibility"]
        score = 0

        reasons = []

        if eligibility["classification"]["available"]:
            score += 50
            reasons.append("Classification is possible")
        targets = analysis_result["targets"]

        if len(targets) > 0:
            if targets[0]["score"] >= 80:
                score += 50
                reasons.append("Strong target candidate detected")

        return ProblemRecommendation(

            problem_type="classification",

            available=(score > 0),

            score=score,

            priority=0,

            reasons=reasons

        )

    def _analyze_clustering(self, analysis_result):

        eligibility = analysis_result["eligibility"]

        score = 0

        reasons = []

        if eligibility["clustering"]["available"]:
            score += 30

            reasons.append("Enough features available for clustering")

        feature_count = len(eligibility["clustering"]["features"])

        if feature_count >= 3:
            score += 20
            reasons.append("Multiple numerical features available")
        rows = analysis_result["profile"]["shape"]["rows"]

        if rows >= 100:
            score += 20
            reasons.append("Dataset size is suitable for clustering")
        targets = analysis_result["targets"]


        strong_targets = [
            target
            for target in targets
            if target["score"] >= 80
        ]

        if len(strong_targets) == 0:
            score += 30
            reasons.append("No target column detected")

        else:

            score -= 20
            reasons.append("Target column exists, classification may be more suitable")

        score = max(score, 0)
        return ProblemRecommendation(

            problem_type="clustering",

            available=(score > 0),

            score=score,

            priority=0,

            reasons=reasons

        )