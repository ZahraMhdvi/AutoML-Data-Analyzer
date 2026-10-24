
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ml_engine.errors import AppError


RULE_NAME = "weighted_mean_ecdf_rank_quantile_binning"
RULE_VERSION = "2.0"
DEFINITION_VERSION = 2
GRID_POINTS = 201

LABELS_BY_BIN_COUNT = {
    2: ["Low", "High"],
    3: ["Low", "Medium", "High"],
    4: ["Low", "Medium", "High", "Very High"],
}


def _usable_numeric(frame, column):
    series = frame[column]
    return (
        pd.api.types.is_numeric_dtype(series)
        and not pd.api.types.is_bool_dtype(series)
        and series.notna().sum() > 0
    )


class PseudoTargetRule:

    def __init__(self, features, directions=None, weights=None, n_classes=3):
        self.features = list(features)
        self.directions = {feature: int(np.sign((directions or {}).get(feature, 1)) or 1) for feature in self.features}
        self.weights = {feature: float((weights or {}).get(feature, 1.0)) for feature in self.features}
        self.n_classes = int(n_classes)
        self.fitted = None


    def fit(self, frame):
        usable = [feature for feature in self.features if feature in frame.columns and _usable_numeric(frame, feature)]
        excluded = [feature for feature in self.features if feature not in usable]

        if not usable:
            raise AppError("PSEUDO_TARGET_NO_NUMERIC")

        grids, fills = {}, {}
        for feature in usable:
            values = frame[feature].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
            probabilities = np.linspace(0.0, 1.0, GRID_POINTS)
            quantiles = np.quantile(values.to_numpy(), probabilities)
            grids[feature] = {"x": quantiles.tolist(), "p": probabilities.tolist()}
            fills[feature] = float(values.median())

        self.fitted = {"usable_features": usable, "excluded_features": excluded, "grids": grids, "fill_values": fills}

        scores = self.score(frame)

        for bins in sorted({self.n_classes, 3, 2}, reverse=True):
            if bins > self.n_classes:
                continue
            cutoffs = np.unique(np.quantile(scores.to_numpy(), np.linspace(0, 1, bins + 1)[1:-1]))
            if len(cutoffs) >= 1 and scores.nunique() >= 2:
                labels = LABELS_BY_BIN_COUNT[len(cutoffs) + 1]
                self.fitted.update({"cutoffs": cutoffs.tolist(), "class_labels": labels, "n_fit_rows": int(len(frame))})
                assigned = self._bin(scores)
                if assigned.nunique() >= 2:
                    distribution = assigned.value_counts()
                    self.fitted["train_distribution"] = {label: int(distribution.get(label, 0)) for label in labels}
                    return self

        raise AppError("PSEUDO_TARGET_NO_VARIATION")


    def score(self, frame):
        if self.fitted is None:
            raise RuntimeError("PseudoTargetRule must be fitted before use")

        total = pd.Series(0.0, index=frame.index)
        weight_sum = 0.0

        for feature in self.fitted["usable_features"]:
            grid = self.fitted["grids"][feature]
            values = pd.to_numeric(frame[feature], errors="coerce").replace([np.inf, -np.inf], np.nan)
            values = values.fillna(self.fitted["fill_values"][feature]).to_numpy(dtype=float)
            ranks = _ecdf(values, np.asarray(grid["x"]), np.asarray(grid["p"]))
            if self.directions.get(feature, 1) < 0:
                ranks = 1.0 - ranks
            weight = self.weights.get(feature, 1.0)
            total += weight * ranks
            weight_sum += weight

        return total / (weight_sum or 1.0)

    def _bin(self, scores):
        cutoffs = self.fitted["cutoffs"]
        labels = self.fitted["class_labels"]
        positions = np.searchsorted(np.asarray(cutoffs), scores.to_numpy(), side="left")
        return pd.Series([labels[position] for position in positions], index=scores.index, dtype=object)

    def transform(self, frame):
        return self._bin(self.score(frame))


    def to_dict(self):
        return {
            "features": self.features,
            "directions": self.directions,
            "weights": self.weights,
            "n_classes": self.n_classes,
            "fitted": self.fitted,
        }

    @classmethod
    def from_dict(cls, data):
        rule = cls(data["features"], data.get("directions"), data.get("weights"), data.get("n_classes", 3))
        rule.fitted = data.get("fitted")
        return rule


def _ecdf(values, grid_x, grid_p):



    unique_x, inverse = np.unique(grid_x, return_inverse=True)
    if len(unique_x) == 1:
        return np.where(values < unique_x[0], 0.0, np.where(values > unique_x[0], 1.0, 0.5))
    unique_p = np.zeros(len(unique_x))
    np.maximum.at(unique_p, inverse, grid_p)
    return np.interp(values, unique_x, unique_p, left=0.0, right=1.0)




def new_definition(features, source, directions=None, weights=None, reason=None, llm_record=None,
                   n_classes=3):


    return {
        "target_type": "pseudo",
        "source": source,
        "target_column": "generated_target",
        "features": list(features),
        "directions": {feature: int((directions or {}).get(feature, 1)) for feature in features},
        "weights": {feature: float((weights or {}).get(feature, 1.0)) for feature in features},
        "n_classes": n_classes,
        "rule": {
            "name": RULE_NAME,
            "version": RULE_VERSION,
            "formula": "s(x) = sum_f w_f * ECDF_f(x_f) / sum_f w_f ; label = quantile bin of s(x) with train cut-offs",
        },
        "missing_policy": "train_median_per_feature",
        "fit_scope": "version_1_training_split",
        "label_policy": "frozen_rule_option_a",
        "reason": reason or {},
        "llm": llm_record,
        "definition_version": DEFINITION_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fitted_rule": None,
    }


def fit_definition(definition, train_frame):


    rule = PseudoTargetRule(
        definition["features"], definition.get("directions"), definition.get("weights"),
        definition.get("n_classes", 3),
    ).fit(train_frame)
    fitted = dict(definition)
    fitted["fitted_rule"] = rule.to_dict()
    return fitted, rule


def rule_from_definition(definition):
    if not definition.get("fitted_rule"):
        return None
    return PseudoTargetRule.from_dict(definition["fitted_rule"])


def build_statistical_definition(dataframe, max_features=3, llm_record=None):


    from ml_engine.preprocessing.pipeline import is_identifier_column

    numeric = [
        column
        for column in dataframe.columns
        if pd.api.types.is_numeric_dtype(dataframe[column])
        and not pd.api.types.is_bool_dtype(dataframe[column])
        and not is_identifier_column(dataframe, column)
        and dataframe[column].nunique(dropna=True) > 2
    ]

    if not numeric:
        raise AppError("PSEUDO_TARGET_NO_NUMERIC")

    directions = {}

    if len(numeric) == 1:
        chosen = numeric
        directions = {numeric[0]: 1}
    else:
        values = dataframe[numeric].astype(float).replace([np.inf, -np.inf], np.nan)
        values = values.fillna(values.median())
        std = values.std(ddof=0).replace(0, 1)
        standardized = (values - values.mean()) / std

        _, _, vt = np.linalg.svd(standardized.to_numpy(), full_matrices=False)
        loadings = pd.Series(vt[0], index=numeric)

        dominant_sign = np.sign(loadings[loadings.abs().idxmax()]) or 1.0
        loadings = loadings * dominant_sign
        same_direction = loadings[loadings > 0]

        chosen = same_direction.sort_values(ascending=False).head(max_features).index.tolist()
        if len(chosen) < 2:
            chosen = loadings.abs().sort_values(ascending=False).head(min(max_features, len(numeric))).index.tolist()
        directions = {feature: int(np.sign(loadings[feature]) or 1) for feature in chosen}

    return new_definition(
        chosen,
        source="statistical",
        directions=directions,
        reason={"code": "STATISTICAL_PCA", "params": {"features": chosen}},
        llm_record=llm_record,
    )


def label_drift(definition, frozen_rule, train_frame, full_frame):

    try:
        _, refitted = fit_definition(definition, train_frame)
    except AppError:
        return None
    frozen = frozen_rule.transform(full_frame)
    refit = refitted.transform(full_frame)
    changed = int((frozen != refit).sum())
    return {
        "rows": int(len(full_frame)),
        "changed": changed,
        "changed_ratio": round(changed / max(len(full_frame), 1), 4),
        "refit_cutoffs": refitted.fitted["cutoffs"],
        "frozen_cutoffs": frozen_rule.fitted["cutoffs"],
    }


def normalized_entropy(labels):

    p = pd.Series(labels).value_counts(normalize=True).to_numpy()
    if len(p) < 2:
        return 0.0
    return float(-(p * np.log(p)).sum() / np.log(len(p)))
