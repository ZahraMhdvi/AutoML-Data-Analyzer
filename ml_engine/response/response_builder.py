from ml_engine.response.recommendation_response import (RecommendationResponse)
from ml_engine.explanation.explanation_engine import (ExplanationEngine)


class ResponseBuilder:

    def __init__(self):
        self.explanation_engine = ExplanationEngine()


    def build(self,score_results,algorithms):

        responses = []

        for index, result in enumerate(
            score_results
        ):


            explanation = (
                self.explanation_engine.generate(

                    result,
                    algorithms[result.algorithm_name]

                )
            )

            response = RecommendationResponse(

                algorithm=explanation["algorithm"],
                score=explanation["score"],
                rank=index + 1,
                reasons=explanation["reasons"],
                limitations=explanation["limitations"]
            )

            responses.append(response)

        return responses