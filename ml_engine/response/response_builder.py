from ml_engine.response.recommendation_response import RecommendationResponse


HIGH_BAND = 70.0
MEDIUM_BAND = 50.0


class ResponseBuilder:

    @staticmethod
    def get_compatibility(score):
        if score >= HIGH_BAND:
            return "high"
        if score >= MEDIUM_BAND:
            return "medium"
        return "low"

    def build(self, score_results, algorithms=None):
        return [
            RecommendationResponse(
                algorithm=result.algorithm_name,
                score=result.score,
                compatibility=self.get_compatibility(result.score),
                rank=index + 1,
                reasons=result.reasons,
                limitations=result.limitations,
                evidence_considered=result.evidence_considered,
                raw_points=result.raw,
                max_points=result.bound,
            )
            for index, result in enumerate(score_results)
        ]
