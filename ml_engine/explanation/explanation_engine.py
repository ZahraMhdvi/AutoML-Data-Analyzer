
class ExplanationEngine:

    def generate(self, score_result, algorithm_info):
        return {
            "algorithm": score_result.algorithm_name,
            "score": score_result.score,
            "reasons": [item["code"] for item in score_result.reasons],
            "limitations": list(algorithm_info.get("weaknesses", [])),
        }
