
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from ml_engine.model_execution.runner import run_classification
from ml_engine.model_execution.split_manager import batch_split
from ml_engine.preprocessing.pipeline import PreprocessingPipeline


def _frame(n=200, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "age": rng.normal(40, 10, n).round(1),
        "income": rng.normal(5000, 800, n).round(0),
        "city": rng.choice(["A", "B", "C"], n),
        "member": rng.choice(["yes", "no"], n),
    })
    df.loc[rng.choice(n, 15, replace=False), "age"] = np.nan
    df["label"] = np.where(df["income"] + rng.normal(0, 300, n) > 5000, "high", "low")
    return df


def test_extreme_test_value_does_not_change_learned_statistics():
    df = _frame()
    train, test, _ = batch_split(len(df), labels=df["label"].to_numpy())
    X = df.drop(columns=["label"])

    clean = PreprocessingPipeline().fit(X.iloc[train])

    mutated = X.copy()
    mutated.loc[mutated.index[test[0]], "income"] = 1e12
    mutated.loc[mutated.index[test[1]], "age"] = np.nan
    refit = PreprocessingPipeline().fit(mutated.iloc[train])

    assert clean.imputer_.fill_values_ == refit.imputer_.fill_values_
    assert clean.scaler_.mean_ == refit.scaler_.mean_
    assert clean.scaler_.scale_ == refit.scaler_.scale_


def test_runner_statistics_are_independent_of_test_rows():
    df = _frame()
    base = run_classification(df, "Logistic Regression", {"type": "observed", "column": "label"},
                              compute_cv=False, compute_permutation=False)
    test_rows = df.index[batch_split(len(df), labels=df["label"].to_numpy())[1]]
    mutated = df.copy()
    mutated.loc[test_rows, "income"] = 9e9
    other = run_classification(mutated, "Logistic Regression", {"type": "observed", "column": "label"},
                               compute_cv=False, compute_permutation=False)

    a = base["protocol"]["preprocessing"]
    b = other["protocol"]["preprocessing"]
    assert a["scaling"] == b["scaling"]
    assert a["imputation"] == b["imputation"]
    assert a["fitted_on_rows"] == base["data_summary"]["train_rows"]


def test_unseen_test_category_is_handled():
    df = _frame()
    train, test, _ = batch_split(len(df), labels=df["label"].to_numpy())
    X = df.drop(columns=["label"])
    prep = PreprocessingPipeline().fit(X.iloc[train])

    unseen = X.iloc[test].copy()
    unseen.iloc[0, unseen.columns.get_loc("city")] = "NEVER_SEEN"
    out = prep.transform(unseen)

    assert list(out.columns) == prep.feature_names_
    assert prep.encoder_.unseen_counts_["city"] == 1
    assert not out.isna().any().any()


def test_rows_without_target_are_dropped_and_logged_in_sync():
    df = _frame()
    df.loc[[3, 7, 11], "label"] = np.nan
    result = run_classification(df, "Decision Tree", {"type": "observed", "column": "label"},
                                compute_cv=False, compute_permutation=False)
    summary = result["data_summary"]

    assert summary["row_drops"] == [{"reason": "MISSING_TARGET", "count": 3}]
    assert summary["train_rows"] + summary["test_rows"] == len(df) - 3
    dist = summary["class_distribution"]
    assert sum(dist["train"].values()) == summary["train_rows"]
    assert sum(dist["test"].values()) == summary["test_rows"]


def test_no_global_outlier_row_removal():
    df = _frame()
    df.loc[0, "income"] = 1e9
    result = run_classification(df, "Decision Tree", {"type": "observed", "column": "label"},
                                compute_cv=False, compute_permutation=False)
    assert result["data_summary"]["rows_used"] == len(df)
    assert result["protocol"]["outlier_policy"] == "none"


def test_cross_validation_refits_preprocessing_in_every_fold():
    df = _frame()
    X, y = df.drop(columns=["label"]), (df["label"] == "high").astype(int)
    pipeline = Pipeline([("prep", PreprocessingPipeline()), ("model", DecisionTreeClassifier(random_state=0))])
    scores = cross_validate(pipeline, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0),
                            return_estimator=True, return_indices=True)

    fills = []
    for estimator, train_idx in zip(scores["estimator"], scores["indices"]["train"]):
        prep = estimator.named_steps["prep"]
        assert prep.n_train_rows_ == len(train_idx)
        assert prep.scaler_.mean_["income"] == pytest.approx(X.iloc[train_idx]["income"].mean())
        fills.append(prep.imputer_.fill_values_["age"])
    assert len(set(fills)) > 1  # every fold learned its own median


def test_split_counts_and_reasons_are_reported():
    df = _frame()
    df["customer_id"] = range(len(df))
    df["constant"] = 1
    result = run_classification(df, "KNN", {"type": "observed", "column": "label"},
                                compute_cv=False, compute_permutation=False)
    reasons = {d["column"]: d["reason"] for d in result["data_summary"]["dropped_column_reasons"]}
    assert reasons == {"customer_id": "IDENTIFIER", "constant": "CONSTANT"}
    split = result["protocol"]["split"]
    assert split["train_rows"] == 160 and split["test_rows"] == 40
    assert result["protocol"]["stratified"] is True


def test_batch_split_membership_is_stable_across_versions():
    labels_v1 = np.array(["a", "b"] * 50)
    labels_v2 = np.concatenate([labels_v1, np.array(["a", "b"] * 20)])
    _, test_v1, _ = batch_split(100, np.ones(100, int), labels_v1)
    _, test_v2, _ = batch_split(140, np.r_[np.ones(100, int), np.full(40, 2)], labels_v2)
    assert set(test_v1) == set(t for t in test_v2 if t < 100)
