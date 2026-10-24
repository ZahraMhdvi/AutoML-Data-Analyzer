

from collections import Counter

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import (
    accuracy_score,
    adjusted_rand_score,
    balanced_accuracy_score,
    calinski_harabasz_score,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    normalized_mutual_info_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    silhouette_score,
)


MAX_SCATTER_POINTS = 3000
MAX_SILHOUETTE_ROWS = 8000
STABILITY_RUNS = 10
STABILITY_FRACTION = 0.8
STABILITY_MAX_ROWS = 2000
MICRO_CLUSTER_RATIO = 0.01



def classification_metrics(y_true, y_pred, class_names):


    labels = list(range(len(class_names)))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": matrix.astype(int).tolist(),
        "classes": [str(name) for name in class_names],
        "per_class": [
            {"class": str(name), "precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
            for i, name in enumerate(class_names)
        ],
        "test_size": int(len(y_true)),
    }


def native_importance(model, feature_names):


    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
        method = "impurity_or_gain_importance"
    elif hasattr(model, "coef_"):
        values = np.abs(np.asarray(model.coef_, dtype=float)).mean(axis=0)
        method = "mean_absolute_coefficient"
    else:
        return None
    total = float(values.sum()) or 1.0
    return {
        "method": method,
        "values": [
            {"feature": str(name), "importance": float(value) / total}
            for name, value in zip(feature_names, values)
        ],
    }



def _valid_for_internal(X, labels):


    mask = labels != -1
    k = len(set(labels[mask]))
    defined = k >= 2 and mask.sum() > k
    return mask, k, defined


def internal_metrics(X, labels, seed=42):
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    mask, k, defined = _valid_for_internal(X, labels)

    result = {
        "silhouette_score": None,
        "davies_bouldin_index": None,
        "calinski_harabasz_index": None,
        "metrics_scope": "non_noise_points",
        "evaluated_points": int(mask.sum()),
    }

    if not defined:
        return result

    Xv, lv = X[mask], labels[mask]

    if len(Xv) > MAX_SILHOUETTE_ROWS:
        result["silhouette_score"] = float(silhouette_score(Xv, lv, sample_size=MAX_SILHOUETTE_ROWS, random_state=seed))
        result["silhouette_sampled"] = True
    else:
        result["silhouette_score"] = float(silhouette_score(Xv, lv))

    result["davies_bouldin_index"] = float(davies_bouldin_score(Xv, lv))
    result["calinski_harabasz_index"] = float(calinski_harabasz_score(Xv, lv))
    return result


def external_metrics(labels, reference_labels):


    if reference_labels is None:
        return None
    reference = np.asarray(reference_labels)
    return {
        "adjusted_rand_index": float(adjusted_rand_score(reference, labels)),
        "normalized_mutual_info": float(normalized_mutual_info_score(reference, labels)),
        "note": "reference labels used for reporting only, not for model selection",
    }


def cluster_stability(X, labels, refit, runs=STABILITY_RUNS, fraction=STABILITY_FRACTION, seed=42):


    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    n = len(X)
    rng = np.random.default_rng(seed)

    if n > STABILITY_MAX_ROWS:
        base = rng.choice(n, STABILITY_MAX_ROWS, replace=False)
    else:
        base = np.arange(n)

    m = max(3, int(len(base) * fraction))
    if m >= len(base) or len(set(labels)) < 2:
        return None

    scores = []
    for _ in range(runs):
        sub = rng.choice(base, m, replace=False)
        try:
            sub_labels = refit(X[sub])
        except Exception:
            continue
        scores.append(adjusted_rand_score(labels[sub], sub_labels))

    if not scores:
        return None

    return {
        "method": "subsample_refit_ari",
        "runs": len(scores),
        "subsample_fraction": fraction,
        "mean_ari": float(np.mean(scores)),
        "std_ari": float(np.std(scores)),
    }


def cluster_profiles(raw_frame, labels, top=3):



    numeric = raw_frame.select_dtypes(include="number")
    numeric = numeric.loc[:, [c for c in numeric.columns if numeric[c].nunique(dropna=True) > 1]]
    if numeric.empty:
        return []

    overall_mean = numeric.mean()
    overall_std = numeric.std(ddof=0).replace(0, 1.0)

    profiles = []
    for cluster in sorted(set(labels)):
        members = numeric[np.asarray(labels) == cluster]
        if members.empty:
            continue
        mean = members.mean()
        z = ((mean - overall_mean) / overall_std).fillna(0.0)
        ordered = z.abs().sort_values(ascending=False).head(top).index
        profiles.append({
            "cluster": int(cluster),
            "is_noise": bool(cluster == -1),
            "size": int(len(members)),
            "important_features": [
                {
                    "feature": str(feature),
                    "cluster_mean": _safe(mean[feature]),
                    "overall_mean": _safe(overall_mean[feature]),
                    "z_difference": _safe(z[feature]),
                    "direction": "above_average" if z[feature] > 0 else "below_average",
                }
                for feature in ordered
            ],
        })
    return profiles


def clustering_metrics(X, labels, raw_frame=None, reference_labels=None, refit=None, seed=42):
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    n = len(labels)

    clusters = sorted(set(labels) - {-1})
    sizes = Counter(labels)
    noise = int(sizes.get(-1, 0))

    warnings = []
    if len(clusters) < 2:
        warnings.append("SINGLE_CLUSTER")
    micro = [int(c) for c in clusters if sizes[c] < max(2, MICRO_CLUSTER_RATIO * n)]
    if micro:
        warnings.append("MICRO_CLUSTERS")
    if n < 30:
        warnings.append("SMALL_DATASET")

    result = {
        "cluster_count": len(clusters),
        "noise_points": noise,
        "noise_ratio": noise / n if n else 0.0,
        "cluster_sizes": {str(int(c)): int(sizes[c]) for c in clusters},
        "micro_clusters": micro,
        "warnings": warnings,
        "rows": int(n),
        "interpretation_note": "internal indices measure geometric cohesion/separation, not domain meaning",
    }

    result.update(internal_metrics(X, labels, seed))
    result["external"] = external_metrics(labels, reference_labels)
    result["stability"] = cluster_stability(X, labels, refit, seed=seed) if refit and len(clusters) >= 2 else None

    result["cluster_points"] = _projection(X, labels)
    if raw_frame is not None:
        result["cluster_profiles"] = cluster_profiles(raw_frame, labels)

    return result


def _projection(X, labels):
    if len(X) == 0:
        return []
    components = min(2, X.shape[1], X.shape[0])
    reduced = PCA(n_components=components).fit_transform(X) if components >= 1 else np.zeros((len(X), 1))
    if reduced.shape[1] < 2:
        reduced = np.column_stack([reduced[:, 0], np.zeros(len(reduced))])
    step = max(1, int(np.ceil(len(labels) / MAX_SCATTER_POINTS)))
    return [
        {"x": float(point[0]), "y": float(point[1]), "cluster": int(label)}
        for point, label in zip(reduced[::step], labels[::step])
    ]


def _safe(value):
    value = float(value)
    return None if np.isnan(value) or np.isinf(value) else round(value, 6)


class ModelEvaluator:



    def evaluate(self, model, X, y=None, problem_type=None):
        if problem_type == "classification":
            predictions = model.predict(X)
            classes = sorted(set(np.asarray(y).tolist()) | set(np.asarray(predictions).tolist()))
            index = {c: i for i, c in enumerate(classes)}
            return classification_metrics([index[v] for v in y], [index[v] for v in predictions], classes)
        if problem_type == "clustering":
            return clustering_metrics(X, model.labels_, raw_frame=pd.DataFrame(X))
        raise ValueError("Unsupported problem type")
