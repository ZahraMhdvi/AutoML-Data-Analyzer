
from ml_engine.problem_selection.problem_report import ProblemRecommendation


RECOMMENDED = "recommended"
POTENTIALLY_SUITABLE = "potentially_suitable"
NOT_SUITABLE = "not_suitable"

STATUS_RANK = {RECOMMENDED: 0, POTENTIALLY_SUITABLE: 1, NOT_SUITABLE: 2}

MIN_ROWS = 10
COMFORT_ROWS = 30


def _strong_targets(analysis_result, dataframe=None):
    strong = []
    for target in analysis_result["targets"]:
        if target["score"] < 80:
            continue
        if dataframe is not None:
            counts = dataframe[target["column"]].dropna().astype(str).value_counts()
            if not (2 <= len(counts) <= 20) or counts.min() < 2:
                continue
        strong.append(target)
    return strong


class ProblemRecommendationEngine:

    def recommend(self, analysis_result):
        dataframe = analysis_result.get("dataframe")
        rows = analysis_result["profile"]["shape"]["rows"]
        columns = analysis_result["columns"]

        usable = [c for c, info in columns.items() if info["semantic_type"] in ("numerical", "categorical")]
        numeric = [c for c, info in columns.items() if info["semantic_type"] == "numerical"]
        strong = _strong_targets(analysis_result, dataframe)
        candidates = analysis_result["targets"]

        classification = self._classification(rows, usable, numeric, strong, candidates)
        clustering = self._clustering(rows, usable, numeric, strong)

        ordered = sorted([classification, clustering], key=lambda r: (STATUS_RANK[r.status], r.problem_type != "classification"))
        for index, recommendation in enumerate(ordered, start=1):
            recommendation.priority = index

        return {"classification": classification, "clustering": clustering}

    @staticmethod
    def _classification(rows, usable, numeric, strong, candidates):
        evidence = []
        if rows < MIN_ROWS:
            evidence.append({"code": "TOO_FEW_ROWS", "params": {"rows": rows, "min_rows": MIN_ROWS}})
        if not usable:
            evidence.append({"code": "NO_USABLE_FEATURES", "params": {}})
        if not candidates and not numeric:
            evidence.append({"code": "NO_TARGET_AND_NO_NUMERIC", "params": {}})

        if evidence:
            status = NOT_SUITABLE
        elif strong and rows >= COMFORT_ROWS:
            status = RECOMMENDED
            evidence.append({"code": "STRONG_TARGET_FOUND", "params": {"column": strong[0]["column"]}})
        else:
            status = POTENTIALLY_SUITABLE
            if strong:
                evidence.append({"code": "STRONG_TARGET_FOUND", "params": {"column": strong[0]["column"]}})
            elif candidates:
                evidence.append({"code": "WEAK_TARGET_ONLY", "params": {"column": candidates[0]["column"]}})
            else:
                evidence.append({"code": "PSEUDO_TARGET_REQUIRED", "params": {}})
            if rows < COMFORT_ROWS:
                evidence.append({"code": "SMALL_DATASET", "params": {"rows": rows}})

        evidence.append({"code": "USABLE_FEATURES", "params": {"count": len(usable)}})
        return ProblemRecommendation("classification", status != NOT_SUITABLE, status, 0, evidence)

    @staticmethod
    def _clustering(rows, usable, numeric, strong):
        evidence = []
        if rows < MIN_ROWS:
            evidence.append({"code": "TOO_FEW_ROWS", "params": {"rows": rows, "min_rows": MIN_ROWS}})
        if len(usable) < 2:
            evidence.append({"code": "TOO_FEW_FEATURES", "params": {"count": len(usable)}})

        if evidence:
            status = NOT_SUITABLE
        elif len(numeric) >= 2 and rows >= COMFORT_ROWS and not strong:
            status = RECOMMENDED
            evidence.append({"code": "NO_STRONG_TARGET", "params": {}})
        else:
            status = POTENTIALLY_SUITABLE
            if strong:
                evidence.append({"code": "TARGET_EXISTS_CLASSIFICATION_LIKELY", "params": {"column": strong[0]["column"]}})
            if len(numeric) < 2:
                evidence.append({"code": "FEW_NUMERIC_FEATURES", "params": {"count": len(numeric)}})
            if rows < COMFORT_ROWS:
                evidence.append({"code": "SMALL_DATASET", "params": {"rows": rows}})

        evidence.append({"code": "NUMERIC_FEATURES", "params": {"count": len(numeric)}})
        return ProblemRecommendation("clustering", status != NOT_SUITABLE, status, 0, evidence)
