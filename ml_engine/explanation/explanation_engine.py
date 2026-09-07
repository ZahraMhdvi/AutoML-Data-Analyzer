from ml_engine.explanation.explanation_templates import (
    EXPLANATION_TEMPLATES
)



class ExplanationEngine:


    def generate(self,score_result,algorithm_info):

        reasons = []
        limitations = []

        for item in score_result.matched:

            if item in EXPLANATION_TEMPLATES:
                reasons.append(
                    EXPLANATION_TEMPLATES[item]
                )

        for item in algorithm_info.get(
                "weaknesses",
                []
        ):

            if item in EXPLANATION_TEMPLATES:
                limitations.append(
                    EXPLANATION_TEMPLATES[item]
                )

        return {
            "algorithm": score_result.algorithm_name,
            "score": score_result.score,
            "reasons": reasons,
            "limitations": limitations

        }