from ml_engine.response.recommendation_response import (RecommendationResponse)
from ml_engine.explanation.explanation_engine import (ExplanationEngine)


class ResponseBuilder:

    def __init__(self):
        self.explanation_engine = ExplanationEngine()

    def get_compatibility(self,score):

        if score >= 70:
            return "high"

        elif score >= 40:
            return "medium"

        else:
            return "low"


    def build(self,score_results,algorithms ):
        responses = []

        filtered_results = [

            result
            for result in score_results
            if result.score > 0

        ]

        for index, result in enumerate(
                filtered_results
        ):
            explanation = (
                self.explanation_engine.generate(

                    result,

                    algorithms[
                        result.algorithm_name
                    ]

                )
            )

            response = RecommendationResponse(

                algorithm=explanation["algorithm"],

                score=explanation["score"],

                compatibility=self.get_compatibility(explanation["score"]),

                rank=index + 1,

                reasons=explanation["reasons"],

                limitations=explanation["limitations"]

            )

            responses.append(response)

        return responses