

import time

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from ml_engine.ai.target_generator import (
    fit_definition,
    label_drift,
    normalized_entropy,
    rule_from_definition,
)
from ml_engine.errors import AppError
from ml_engine.model_execution.evaluator import (
    classification_metrics,
    clustering_metrics,
    native_importance,
)
from ml_engine.model_execution.split_manager import DEFAULT_SEED, DEFAULT_TEST_SIZE, batch_split
from ml_engine.model_execution.trainer import build_classifier, build_clusterer, clone_clusterer
from ml_engine.model_selection.algorithm_registry import CLASSIFICATION_ALGORITHMS, CLUSTERING_ALGORITHMS
from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.provenance import environment_versions
from ml_engine.validation import raise_on_errors, validate_dataframe


ModelRunError = AppError

CV_MAX_TRAIN_ROWS = 20000
PERMUTATION_REPEATS = 5
PERMUTATION_MAX_ROWS = 3000


def _ms(start):
    return round((time.perf_counter() - start) * 1000, 2)




def _fit_predict(algorithm, X_train_raw, y_train, X_test_raw, seed, outlier_policy="none"):
    prep = PreprocessingPipeline(problem_type="classification", outlier_policy=outlier_policy).fit(X_train_raw)
    X_train = prep.transform(X_train_raw)
    X_test = prep.transform(X_test_raw)

    if X_train.shape[1] == 0:
        raise AppError("NO_USABLE_FEATURES")

    model, params = build_classifier(algorithm, len(X_train), seed)

    start = time.perf_counter()
    model.fit(X_train, y_train)
    train_ms = _ms(start)

    start = time.perf_counter()
    predictions = model.predict(X_test)
    inference_ms = _ms(start)

    return prep, model, params, np.asarray(predictions).astype(int), train_ms, inference_ms


def _cross_validation(algorithm, X_train_raw, y_train, seed, folds):
    counts = np.bincount(y_train)
    counts = counts[counts > 0]
    n_splits = int(min(folds, counts.min())) if len(counts) else 0

    if n_splits < 2:
        return {"skipped": "CLASS_TOO_SMALL_FOR_CV"}
    if len(X_train_raw) > CV_MAX_TRAIN_ROWS:
        return {"skipped": "DATASET_TOO_LARGE_FOR_CV"}

    model, _ = build_classifier(algorithm, int(len(X_train_raw) * (n_splits - 1) / n_splits), seed)
    pipeline = Pipeline([("prep", PreprocessingPipeline(problem_type="classification")), ("model", model)])
    scores = cross_validate(
        pipeline, X_train_raw, y_train,
        cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed),
        scoring={"accuracy": "accuracy", "macro_f1": "f1_macro", "balanced_accuracy": "balanced_accuracy",
                 "weighted_f1": "f1_weighted"},
        error_score=np.nan,
    )
    summary = {"folds": n_splits, "scope": "training_split_only", "pipeline_refit_per_fold": True}
    for name in ("accuracy", "macro_f1", "balanced_accuracy", "weighted_f1"):
        values = scores[f"test_{name}"]
        summary[name] = {"mean": float(np.nanmean(values)), "std": float(np.nanstd(values))}
    return summary


def _permutation(prep, model, X_test_raw, y_test, seed):
    estimator = Pipeline([("prep", prep), ("model", model)])
    max_samples = min(1.0, PERMUTATION_MAX_ROWS / max(len(X_test_raw), 1))
    result = permutation_importance(
        estimator, X_test_raw, y_test, scoring="f1_macro", n_repeats=PERMUTATION_REPEATS,
        random_state=seed, max_samples=max_samples,
    )
    used = set(prep.selector_.kept_)
    values = [
        {"feature": str(column), "importance": float(mean), "std": float(std)}
        for column, mean, std in zip(X_test_raw.columns, result.importances_mean, result.importances_std)
        if column in used
    ]
    values.sort(key=lambda item: item["importance"], reverse=True)
    return {
        "method": "permutation_importance",
        "scope": "independent_test_split",
        "scoring": "macro_f1_drop",
        "n_repeats": PERMUTATION_REPEATS,
        "values": values,
        "note": "importance reflects predictive association in this model, not causation",
    }


def _condition_metrics(algorithm, train_raw, y_train, test_raw, y_test, classes, seed):
    if train_raw.shape[1] == 0:
        return None
    try:
        _, _, _, predictions, _, _ = _fit_predict(algorithm, train_raw, y_train, test_raw, seed)
    except AppError:
        return None
    metrics = classification_metrics(y_test, predictions, classes)
    return {key: metrics[key] for key in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1")}


def run_classification(df, algorithm, target_info, batch_ids=None, seed=DEFAULT_SEED,
                       test_size=DEFAULT_TEST_SIZE, cv_folds=5, compute_cv=True,
                       compute_permutation=True, outlier_policy="none"):


    total_start = time.perf_counter()

    if algorithm not in CLASSIFICATION_ALGORITHMS:
        raise AppError("ALGORITHM_UNKNOWN", {"algorithm": algorithm})
    if df is None or df.empty:
        raise AppError("DATASET_NO_ROWS")

    target_type = target_info.get("type", "observed")
    batch_ids = np.ones(len(df), dtype=int) if batch_ids is None else np.asarray(batch_ids)
    df = df.reset_index(drop=True)
    initial_rows = int(len(df))
    row_drops = []
    definition = None

    if target_type == "pseudo":
        definition = dict(target_info["definition"])
        target_column = definition.get("target_column", "generated_target")
        frame = df.drop(columns=[target_column], errors="ignore")
        issues = validate_dataframe(frame)
        raise_on_errors(issues)

        train_pos, test_pos, split_info = batch_split(len(frame), batch_ids, None, test_size, seed)

        rule = rule_from_definition(definition)
        if rule is None:
            first_batch = batch_ids.min()
            fit_rows = train_pos[batch_ids[train_pos] == first_batch]
            definition, rule = fit_definition(definition, frame.iloc[fit_rows])
        labels = rule.transform(frame)
        generator_features = list(rule.fitted["usable_features"])
        features = frame
    else:
        target_column = target_info.get("column")
        if not target_column or target_column not in df.columns:
            raise AppError("TARGET_NOT_FOUND")

        missing_target = df[target_column].isna().to_numpy()
        if missing_target.any():
            row_drops.append({"reason": "MISSING_TARGET", "count": int(missing_target.sum())})
            df = df.loc[~missing_target].reset_index(drop=True)
            batch_ids = batch_ids[~missing_target]

        issues = validate_dataframe(df, target=target_column)
        raise_on_errors(issues)

        labels = df[target_column].astype(str)
        features = df.drop(columns=[target_column])
        train_pos, test_pos, split_info = batch_split(len(df), batch_ids, labels.to_numpy(), test_size, seed)
        generator_features = []

    counts = labels.value_counts()
    if len(counts) < 2:
        raise AppError("TARGET_TOO_FEW_CLASSES")

    encoder = LabelEncoder().fit(labels.iloc[train_pos])
    if target_type == "pseudo":

        ordered = [c for c in rule.fitted["class_labels"] if c in set(labels.iloc[train_pos])]
        encoder.classes_ = np.asarray(ordered, dtype=object)
    class_names = [str(c) for c in encoder.classes_]
    y_train = encoder.transform(labels.iloc[train_pos])
    test_known = labels.iloc[test_pos].isin(class_names).to_numpy()
    if not test_known.all():
        row_drops.append({"reason": "TEST_CLASS_UNSEEN_IN_TRAIN", "count": int((~test_known).sum())})
        test_pos = test_pos[test_known]
    y_test = encoder.transform(labels.iloc[test_pos])

    X_train_raw = features.iloc[train_pos]
    X_test_raw = features.iloc[test_pos]

    prep, model, params, predictions, train_ms, inference_ms = _fit_predict(
        algorithm, X_train_raw, y_train, X_test_raw, seed, outlier_policy)

    metrics = classification_metrics(y_test, predictions, class_names)
    metrics["latency"] = {"train_ms": train_ms, "inference_ms": inference_ms}

    importance = {
        "permutation": _permutation(prep, model, X_test_raw, y_test, seed) if compute_permutation else None,
        "native": native_importance(model, prep.feature_names_),
    }

    if importance["permutation"]:
        metrics["feature_importance"] = [
            {"feature": item["feature"], "importance": max(item["importance"], 0.0)}
            for item in importance["permutation"]["values"]
        ]

    cv = _cross_validation(algorithm, X_train_raw, y_train, seed, cv_folds) if compute_cv else None

    ablation = None
    if target_type == "pseudo":
        independent = [c for c in features.columns if c not in generator_features]
        condition_b = _condition_metrics(
            algorithm, X_train_raw[independent], y_train, X_test_raw[independent], y_test, class_names, seed)
        reconstruct = _condition_metrics(
            algorithm, X_train_raw[generator_features], y_train, X_test_raw[generator_features], y_test,
            class_names, seed)
        condition_a = {key: metrics[key] for key in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1")}
        ablation = {
            "generator_features": generator_features,
            "condition_a_with_generator_features": condition_a,
            "condition_b_without_generator_features": condition_b,
            "independent_feature_count": len(independent),
            "delta_macro_f1": (condition_a["macro_f1"] - condition_b["macro_f1"]) if condition_b else None,
            "delta_accuracy": (condition_a["accuracy"] - condition_b["accuracy"]) if condition_b else None,
            "reconstructability_R": reconstruct["accuracy"] if reconstruct else None,
            "normalized_entropy_H": normalized_entropy(labels.iloc[train_pos]),
            "interpretation": "Condition A measures reconstruction of a synthetic rule; "
                              "Condition B measures independent predictive signal.",
        }
        if len(set(batch_ids.tolist())) > 1:
            first_train = train_pos[batch_ids[train_pos] == batch_ids.min()]
            all_train_frame = frame.iloc[train_pos]
            ablation["label_drift_if_regenerated"] = label_drift(definition, rule, all_train_frame, frame)
            ablation["label_drift_if_regenerated"]["frozen_fit_rows"] = int(len(first_train))


    first_batch_mask = batch_ids[test_pos] == batch_ids.min()
    fixed_holdout = None
    if first_batch_mask.any() and len(set(batch_ids.tolist())) > 1:
        fh = classification_metrics(y_test[first_batch_mask], predictions[first_batch_mask], class_names)
        fixed_holdout = {key: fh[key] for key in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1")}
        fixed_holdout["rows"] = int(first_batch_mask.sum())
    metrics["fixed_holdout_v1"] = fixed_holdout

    class_distribution = {
        "train": {name: int(np.sum(y_train == i)) for i, name in enumerate(class_names)},
        "test": {name: int(np.sum(y_test == i)) for i, name in enumerate(class_names)},
    }

    result = {
        "algorithm": algorithm,
        "problem_type": "classification",
        "metrics": metrics,
        "cross_validation": cv,
        "feature_importance": importance,
        "ablation": ablation,
        "issues": issues,
        "data_summary": {
            "rows": initial_rows,
            "rows_used": int(len(train_pos) + len(test_pos)),
            "train_rows": int(len(train_pos)),
            "test_rows": int(len(test_pos)),
            "row_drops": row_drops,
            "features": int(len(prep.feature_names_)),
            "input_features": [str(c) for c in prep.selector_.kept_],
            "dropped_columns": [str(c) for c in prep.dropped_columns],
            "dropped_column_reasons": prep.report()["dropped_columns"],
            "class_distribution": class_distribution,
        },
        "protocol": {
            "split": split_info,
            "stratified": all(mode == "stratified" for mode in split_info["modes"].values()),
            "random_seed": seed,
            "hyperparameters": params,
            "preprocessing": prep.report(),
            "label_encoding": class_names,
            "outlier_policy": outlier_policy,
            "environment": environment_versions(),
        },
        "latency_ms": _ms(total_start),
    }
    if definition is not None:
        result["fitted_target_definition"] = definition
        result["target_source"] = definition.get("source")
    return result




def run_clustering(df, algorithm, cluster_count=None, reference_labels=None, seed=DEFAULT_SEED,
                   stability=True):
    total_start = time.perf_counter()

    if algorithm not in CLUSTERING_ALGORITHMS:
        raise AppError("ALGORITHM_UNKNOWN", {"algorithm": algorithm})
    if df is None or df.empty:
        raise AppError("DATASET_NO_ROWS")

    df = df.reset_index(drop=True)
    issues = validate_dataframe(df)
    raise_on_errors(issues)

    if len(df) < 3:
        raise AppError("CLUSTERING_TOO_FEW_ROWS", {"min_rows": 3})

    if cluster_count not in (None, "", 0):
        try:
            cluster_count = int(cluster_count)
        except (TypeError, ValueError):
            raise AppError("CLUSTER_COUNT_INVALID", {"max": len(df) - 1})
        if cluster_count < 2 or cluster_count >= len(df):
            raise AppError("CLUSTER_COUNT_INVALID", {"max": len(df) - 1})
    else:
        cluster_count = None


    prep = PreprocessingPipeline(problem_type="clustering").fit(df)
    X = prep.transform(df)
    if X.shape[1] == 0:
        raise AppError("NO_USABLE_FEATURES")

    model, params, selection = build_clusterer(algorithm, X.to_numpy(), cluster_count, seed)

    start = time.perf_counter()
    labels = np.asarray(model.fit_predict(X.to_numpy()))
    fit_ms = _ms(start)

    def refit(X_sub):
        return clone_clusterer(algorithm, params).fit_predict(X_sub)

    metrics = clustering_metrics(
        X.to_numpy(), labels,
        raw_frame=sanitized_numeric(df, prep),
        reference_labels=reference_labels,
        refit=refit if stability else None,
        seed=seed,
    )
    metrics["latency"] = {"fit_ms": fit_ms}

    return {
        "algorithm": algorithm,
        "problem_type": "clustering",
        "metrics": metrics,
        "issues": issues,
        "data_summary": {
            "rows": int(len(df)),
            "rows_used": int(len(X)),
            "features": int(X.shape[1]),
            "input_features": [str(c) for c in prep.selector_.kept_],
            "dropped_columns": [str(c) for c in prep.dropped_columns],
            "dropped_column_reasons": prep.report()["dropped_columns"],
        },
        "protocol": {
            "random_seed": seed,
            "hyperparameters": params,
            "model_selection": selection,
            "selection_uses_ground_truth": False,
            "preprocessing": prep.report(),
            "environment": environment_versions(),
        },
        "latency_ms": _ms(total_start),
    }


def sanitized_numeric(df, prep):
    kept = [c for c in prep.selector_.kept_ if c in df.columns]
    frame = df[kept].copy()
    for column in prep.coerced_numeric_:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.replace([np.inf, -np.inf], np.nan)




def run_model_on_dataframe(df, algorithm, problem_type, target=None, preferences=None,
                           target_info=None, batch_ids=None, seed=DEFAULT_SEED):
    preferences = preferences or {}

    if problem_type == "classification":
        info = target_info or {"type": "observed", "column": target}
        return run_classification(df, algorithm, info, batch_ids=batch_ids, seed=seed)

    if problem_type == "clustering":
        return run_clustering(df, algorithm, preferences.get("cluster_count"), seed=seed)

    raise AppError("INVALID_PROBLEM_TYPE")
