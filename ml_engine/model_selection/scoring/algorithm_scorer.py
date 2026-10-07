from ml_engine.model_selection.scoring.score_result import (AlgorithmScoreResult)
from ml_engine.model_selection.scoring.capability_matcher import (CapabilityMatcher
                                                                  )
class AlgorithmScorer:


    def __init__(self):

        self.capability_matcher = CapabilityMatcher()

    def score(self,algorithm_name,algorithm_info,preferences,dataset_features):
        score = 0
        matched = []
        unmatched = []

        strengths = algorithm_info["strengths"]
        weaknesses = algorithm_info["weaknesses"]

        expanded_preferences = (
            self.capability_matcher.expand_preferences(
                preferences
            )
        )


        for capability in expanded_preferences:
            if capability in strengths:
                score += 40
                matched.append(capability)

            elif capability in weaknesses:
                score -= 15
                unmatched.append(capability)


        for feature, value in dataset_features.items():

            if not value:
                continue

            if feature in strengths:
                score += 10
                matched.append(feature)

            elif feature in weaknesses:
                score -= 10
                unmatched.append(feature)
        priority_order = [
            "high_accuracy",
            "very_high_accuracy",
            "handles_noise",
            "mixed_features",
            "interpretable",
            "fast"
        ]

        matched = sorted(
            matched,
            key=lambda x: (
                priority_order.index(x)
                if x in priority_order
                else 999
            )
        )
        reasons = []
        limitations = []

        for capability in matched:
            reasons.append(
                f"به دلیل داشتن قابلیت {capability} امتیاز دریافت کرد"
            )

        for capability in unmatched:
            limitations.append(
                f"در قابلیت {capability} محدودیت دارد"
            )

        return AlgorithmScoreResult(

            algorithm_name=algorithm_name,
            score=max(score, 0),
            matched=matched,
            unmatched=unmatched,
            reasons=reasons,
            limitations=limitations
        )