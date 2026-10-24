import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_blobs

from ml_engine.errors import AppError
from ml_engine.model_execution.evaluator import clustering_metrics
from ml_engine.model_execution.runner import run_classification, run_clustering
from ml_engine.validation import schema_changes, validate_dataframe


def _blobs(n=300, centers=3, seed=0):
    X, y = make_blobs(n_samples=n, centers=centers, random_state=seed, cluster_std=0.8)
    return pd.DataFrame(X, columns=["f1", "f2"]), y


def test_complete_internal_metrics_and_stability():
    df, _ = _blobs()
    result = run_clustering(df, "KMeans")
    m = result["metrics"]
    assert m["cluster_count"] == 3
    for key in ("silhouette_score", "davies_bouldin_index", "calinski_harabasz_index"):
        assert m[key] is not None
    assert m["stability"]["mean_ari"] > 0.9
    assert m["external"] is None
    assert result["protocol"]["selection_uses_ground_truth"] is False


def test_reference_labels_are_reporting_only():
    df, y = _blobs()
    with_ref = run_clustering(df, "KMeans", reference_labels=y)
    without = run_clustering(df, "KMeans")
    assert with_ref["protocol"]["hyperparameters"] == without["protocol"]["hyperparameters"]
    assert with_ref["metrics"]["external"]["adjusted_rand_index"] > 0.9


def test_single_cluster_does_not_crash():
    X = np.zeros((20, 2)) + np.random.default_rng(0).normal(0, 1e-3, (20, 2))
    m = clustering_metrics(X, np.zeros(20, dtype=int))
    assert m["silhouette_score"] is None and "SINGLE_CLUSTER" in m["warnings"]


def test_dbscan_noise_is_reported_and_excluded_from_indices():
    X, _ = make_blobs(n_samples=200, centers=2, random_state=1, cluster_std=0.5)
    labels = np.where(np.arange(200) < 20, -1, (X[:, 0] > X[:, 0].mean()).astype(int))
    m = clustering_metrics(X, labels)
    assert m["noise_points"] == 20 and m["noise_ratio"] == pytest.approx(0.1)
    assert m["evaluated_points"] == 180 and m["metrics_scope"] == "non_noise_points"


def test_profiles_use_actual_columns_without_hardcoded_names():
    df, _ = _blobs()
    df["Customer_ID"] = range(len(df))  # treated as identifier by rule, not by a hard-coded name
    df["Churn"] = np.random.default_rng(0).choice([0, 1], len(df))
    result = run_clustering(df, "KMeans", cluster_count=3)
    features = {f["feature"] for p in result["metrics"]["cluster_profiles"] for f in p["important_features"]}
    assert "Customer_ID" not in features
    assert features <= {"f1", "f2", "Churn"}


def test_small_dataset_and_micro_cluster_warnings():
    df = pd.DataFrame({"a": [0, 0.1, 0.2, 5, 5.1, 5.2, 9, 0.15, 5.15, 9.1, 0.05, 5.05]})
    df["b"] = df["a"] * 2
    result = run_clustering(df, "KMeans", cluster_count=3)
    assert "SMALL_DATASET" in result["metrics"]["warnings"]


@pytest.mark.parametrize("frame, code", [
    (pd.DataFrame({"a": range(5), "b": range(5)}), "TOO_FEW_ROWS"),
    (pd.DataFrame({"id": range(40), "c": [1] * 40}), "NO_USABLE_FEATURES"),
])
def test_blocking_issues_raise_coded_errors(frame, code):
    with pytest.raises(AppError) as info:
        run_clustering(frame, "KMeans")
    assert info.value.code == code


def test_warning_level_edge_cases_are_reported_not_raised():
    rng = np.random.default_rng(0)
    n = 120
    df = pd.DataFrame({
        "constant": 1,
        "mostly_null": [np.nan] * 100 + list(range(20)),
        "mixed": [str(i) if i % 30 else "n/a" for i in range(n)],
        "mixed_objects": [i if i % 2 else str(i) + "x" for i in range(n)],
        "inf": np.r_[np.inf, rng.normal(size=n - 1)],
        "many_categories": [f"cat{i % 60}" for i in range(n)],
        "x": rng.normal(size=n),
        "label": ["a"] * 110 + ["b"] * 10,
    })
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)
    codes = {issue["code"] for issue in validate_dataframe(df, target="label")}
    assert {"CONSTANT_COLUMNS", "HIGH_MISSING_COLUMNS", "MIXED_TYPES_COERCED", "MIXED_TYPES", "INFINITE_VALUES",
            "HIGH_CARDINALITY", "DUPLICATE_ROWS", "IMBALANCED_TARGET"} <= codes

    result = run_classification(df, "Random Forest", {"type": "observed", "column": "label"},
                                compute_cv=False, compute_permutation=False)
    reasons = {d["column"]: d["reason"] for d in result["data_summary"]["dropped_column_reasons"]}
    assert reasons["constant"] == "CONSTANT" and reasons["mostly_null"] == "HIGH_MISSING"
    assert "mixed" in result["protocol"]["preprocessing"]["coerced_numeric_columns"]


def test_single_sample_class_is_rejected():
    df = pd.DataFrame({"x": range(40), "y": ["a"] * 20 + ["b"] * 19 + ["c"]})
    with pytest.raises(AppError) as info:
        run_classification(df, "KNN", {"type": "observed", "column": "y"})
    assert info.value.code == "TARGET_SINGLE_SAMPLE_CLASS"


def test_schema_change_detection():
    frame = pd.DataFrame({"a": ["x"], "c": [1]})
    missing, extra, changed = schema_changes(["a", "b"], frame, {"a": "numeric"})
    assert missing == ["b"] and extra == ["c"] and changed == ["a"]
