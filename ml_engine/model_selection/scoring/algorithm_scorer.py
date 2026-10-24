

from ml_engine.model_selection.scoring.capability_matcher import CapabilityMatcher
from ml_engine.model_selection.scoring.score_result import AlgorithmScoreResult


WEIGHTS = {
    "preference": {"strength": 40.0, "weakness": 15.0},
    "data": {"strength": 10.0, "weakness": 10.0},
}
NEUTRAL_SCORE = 50.0


def evidence_items(preferences, dataset_features):
    matcher = CapabilityMatcher()
    items = {}
    for capability in matcher.expand_preferences(preferences or {}):
        items[capability] = "preference"
    for feature, present in (dataset_features or {}).items():
        if present and feature not in items:
            items[feature] = "data"
    return items


class AlgorithmScorer:

    def score(self, algorithm_name, algorithm_info, preferences, dataset_features):
        strengths = set(algorithm_info.get("strengths", []))
        weaknesses = set(algorithm_info.get("weaknesses", []))
        items = evidence_items(preferences, dataset_features)

        raw, bound = 0.0, 0.0
        evidence, matched, unmatched = [], [], []

        for code, source in sorted(items.items()):
            weights = WEIGHTS[source]
            bound += weights["strength"]
            if code in strengths:
                raw += weights["strength"]
                matched.append(code)
                evidence.append({"code": code, "source": source, "effect": "strength", "points": weights["strength"]})
            elif code in weaknesses:
                raw -= weights["weakness"]
                unmatched.append(code)
                evidence.append({"code": code, "source": source, "effect": "weakness", "points": -weights["weakness"]})

        score = NEUTRAL_SCORE if bound == 0 else NEUTRAL_SCORE + 50.0 * raw / bound
        score = round(min(100.0, max(0.0, score)), 1)

        return AlgorithmScoreResult(
            algorithm_name=algorithm_name,
            score=score,
            matched=matched,
            unmatched=unmatched,
            reasons=[item for item in evidence if item["effect"] == "strength"],
            limitations=[item for item in evidence if item["effect"] == "weakness"],
            raw=raw,
            bound=bound,
            evidence_considered=[{"code": code, "source": source} for code, source in sorted(items.items())],
        )
