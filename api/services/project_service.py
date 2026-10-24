

import csv
import io
import json
import logging
import os
import shutil
import uuid

import numpy as np
import pandas as pd

from api.core.db import connect, from_json, now_iso, project_dir, to_json
from api.core.datasets import check_extension, read_dataset_file
from ml_engine.ai.llm_target_service import (
    LLMTargetServiceError,
    build_prompt_profile,
    get_llm_service,
    read_config,
)
from ml_engine.ai.target_generator import (
    build_statistical_definition,
    fit_definition,
    new_definition,
    rule_from_definition,
)
from ml_engine.analysis.application.analysis_application import AnalysisApplication
from ml_engine.column_analyzer import ColumnAnalyzer
from ml_engine.errors import AppError
from ml_engine.model_execution.runner import run_classification, run_clustering
from ml_engine.model_execution.split_manager import DEFAULT_SEED, DEFAULT_TEST_SIZE, batch_split
from ml_engine.model_selection.algorithm_registry import (
    CLASSIFICATION_ALGORITHMS,
    CLUSTERING_ALGORITHMS,
    eligibility,
)
from ml_engine.model_selection.application.model_selection_application import ModelSelectionApplication
from ml_engine.model_selection.data_characteristics import DataCharacteristicsDetector
from ml_engine.provenance import environment_versions
from ml_engine.validation import column_kinds, schema_changes


AI_TARGET_COLUMN = "generated_target"

TARGET_TYPES = {"detected": "observed", "manual": "user_selected", "ai": "pseudo"}

logger = logging.getLogger(__name__)

analysis_application = AnalysisApplication()
model_selection_application = ModelSelectionApplication()
characteristics_detector = DataCharacteristicsDetector()


class WorkflowError(AppError):
    """A user-facing problem with the request (HTTP 400)"""



def get_project_row(conn, user_id, project_id):
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    ).fetchone()
    if row is None:
        raise AppError("PROJECT_NOT_FOUND", status=404)
    return row


def get_versions(conn, project_id):
    return conn.execute(
        "SELECT * FROM versions WHERE project_id = ? ORDER BY version_no", (project_id,)
    ).fetchall()


def load_cumulative_dataframe(project_row, versions, upto_version_no=None, with_batches=False):
    columns = from_json(project_row["columns_json"])
    frames, batches = [], []

    for version in versions:
        if upto_version_no is not None and version["version_no"] > upto_version_no:
            break
        frame = read_dataset_file(version["file_path"])[columns]
        frames.append(frame)
        batches.append(np.full(len(frame), version["version_no"], dtype=int))

    if not frames:
        raise WorkflowError("PROJECT_NO_DATA")

    df = pd.concat(frames, ignore_index=True)
    if with_batches:
        return df, np.concatenate(batches)
    return df


def save_batch_file(project_id, version_no, content, filename):
    ext = check_extension(filename)
    path = os.path.join(project_dir(project_id), f"batch_{version_no}{ext}")
    with open(path, "wb") as handle:
        handle.write(content)
    return path


def save_draft(project_id, updates):
    with connect() as conn:
        row = conn.execute("SELECT draft_json FROM projects WHERE id = ?", (project_id,)).fetchone()
        draft = from_json(row["draft_json"]) or {}
        draft.update(updates)
        conn.execute("UPDATE projects SET draft_json = ?, updated_at = ? WHERE id = ?",
                     (to_json(draft), now_iso(), project_id))
    return draft


def get_draft(project_row):
    return from_json(project_row["draft_json"]) or {}


def load_project_dataframe(user_id, project_id, with_batches=False):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)
    return project, load_cumulative_dataframe(project, versions, with_batches=with_batches)


def log_llm_call(user_id, project_id, record):
    with connect() as conn:
        conn.execute(
            """INSERT INTO llm_calls (request_id, user_id, project_id, requested_method, actual_method,
                   requested_model, successful_model, fallback_used, fallback_reason, latency_ms, status,
                   record_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["request_id"], user_id, project_id, record.get("requested_method"),
             record.get("actual_method"), record.get("requested_model"), record.get("successful_model"),
             int(bool(record.get("fallback_used"))), record.get("fallback_reason"), record.get("latency_ms"),
             record.get("status"), to_json(record), now_iso()),
        )




def _main_metrics(result):
    if not result:
        return None
    metrics = result.get("metrics") or {}
    if result.get("problem_type") == "clustering" or "cluster_count" in metrics:
        return {
            "cluster_count": metrics.get("cluster_count"),
            "silhouette_score": metrics.get("silhouette_score"),
            "davies_bouldin_index": metrics.get("davies_bouldin_index"),
            "calinski_harabasz_index": metrics.get("calinski_harabasz_index"),
            "noise_points": metrics.get("noise_points"),
            "noise_ratio": metrics.get("noise_ratio"),
        }
    fixed = metrics.get("fixed_holdout_v1") or {}
    return {
        "accuracy": metrics.get("accuracy"),
        "balanced_accuracy": metrics.get("balanced_accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
        "macro_f1": metrics.get("macro_f1"),
        "weighted_f1": metrics.get("weighted_f1"),
        "fixed_holdout_macro_f1": fixed.get("macro_f1"),
        "fixed_holdout_accuracy": fixed.get("accuracy"),
    }


def serialize_version(row, include_result=True):
    result = from_json(row["result_json"])
    data = {
        "version_no": row["version_no"],
        "filename": row["filename"],
        "rows_added": row["rows_added"],
        "total_rows": row["total_rows"],
        "status": row["status"],
        "error": from_json(row["error"]) if row["error"] and str(row["error"]).startswith("{") else row["error"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "summary": _main_metrics(result),
        "characteristics": from_json(row["characteristics_json"]),
        "issues": from_json(row["issues_json"]) if "issues_json" in row.keys() else None,
    }
    if include_result:
        data["result"] = result
    return data


def _public_definition(definition):
    if not definition:
        return None
    rule = definition.get("fitted_rule") or {}
    fitted = rule.get("fitted") or {}
    return {
        "source": definition.get("source"),
        "features": definition.get("features"),
        "usable_features": fitted.get("usable_features"),
        "directions": definition.get("directions"),
        "weights": definition.get("weights"),
        "rule": definition.get("rule"),
        "cutoffs": fitted.get("cutoffs"),
        "class_labels": fitted.get("class_labels"),
        "train_distribution": fitted.get("train_distribution"),
        "fit_scope": definition.get("fit_scope"),
        "label_policy": definition.get("label_policy"),
        "missing_policy": definition.get("missing_policy"),
        "reason": definition.get("reason"),
        "llm": definition.get("llm"),
        "definition_version": definition.get("definition_version"),
        "created_at": definition.get("created_at"),
    }


def _public_config(config):
    if not config:
        return None
    public = dict(config)
    definition = public.pop("ai_definition", None)
    if definition:
        public["ai_target"] = _public_definition(definition)
    return public


def serialize_project(row, versions, include_details=True):
    config = from_json(row["config_json"])
    latest = versions[-1] if versions else None
    completed = [v for v in versions if v["status"] == "completed"]

    data = {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "columns": from_json(row["columns_json"]),
        "config": _public_config(config),
        "version_count": len(versions),
        "total_rows": latest["total_rows"] if latest else 0,
        "latest_summary": _main_metrics(from_json(completed[-1]["result_json"])) if completed else None,
    }
    if include_details:
        data["analysis"] = from_json(row["analysis_json"])
        draft = get_draft(row)
        if draft.get("ai_definition"):
            draft = dict(draft)
            draft["ai_target"] = _public_definition(draft.pop("ai_definition"))
        data["draft"] = draft
        data["versions"] = [serialize_version(v) for v in versions]
    return data


# ---------------------------------------------------------------------------
# projects and versions
# ---------------------------------------------------------------------------

def create_project(user_id, name, filename, content, dataframe):
    analysis = analysis_application.analyze_dataframe(dataframe)
    timestamp = now_iso()

    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO projects (user_id, name, status, columns_json, analysis_json, column_kinds_json,
                   created_at, updated_at)
               VALUES (?, ?, 'draft', ?, ?, ?, ?, ?)""",
            (user_id, name, to_json(list(dataframe.columns)), to_json(analysis),
             to_json(column_kinds(dataframe)), timestamp, timestamp),
        )
        project_id = cursor.lastrowid
        try:
            path = save_batch_file(project_id, 1, content, filename)
        except Exception:
            shutil.rmtree(project_dir(project_id), ignore_errors=True)
            raise
        conn.execute(
            """INSERT INTO versions (project_id, version_no, filename, file_path, rows_added, total_rows, status,
                   created_at, issues_json)
               VALUES (?, 1, ?, ?, ?, ?, 'pending', ?, ?)""",
            (project_id, filename, path, len(dataframe), len(dataframe), timestamp, to_json(analysis.get("issues"))),
        )
    return project_id


def check_batch_schema(project_row, dataframe):
    expected = from_json(project_row["columns_json"])
    kinds = from_json(project_row["column_kinds_json"]) if "column_kinds_json" in project_row.keys() else None
    missing, extra, changed = schema_changes(expected, dataframe, kinds)
    if missing or extra:
        raise WorkflowError("SCHEMA_MISMATCH", {"missing": missing or ["-"], "extra": extra or ["-"]})
    issues = []
    if changed:
        issues.append({"code": "SCHEMA_TYPE_CHANGED", "severity": "warning", "params": {"columns": changed}})
    duplicates = int(dataframe.duplicated().sum())
    if duplicates:
        issues.append({"code": "DUPLICATE_ROWS", "severity": "info", "params": {"count": duplicates}})
    return issues


def add_version(user_id, project_id, filename, content, dataframe):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        if project["status"] != "ready":
            raise WorkflowError("PROJECT_NOT_READY")
        issues = check_batch_schema(project, dataframe)
        versions = get_versions(conn, project_id)
        version_no = versions[-1]["version_no"] + 1
        total_rows = versions[-1]["total_rows"] + len(dataframe)
        path = save_batch_file(project_id, version_no, content, filename)
        conn.execute(
            """INSERT INTO versions (project_id, version_no, filename, file_path, rows_added, total_rows, status,
                   created_at, issues_json)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (project_id, version_no, filename, path, len(dataframe), total_rows, now_iso(), to_json(issues)),
        )

    try:
        run_version(user_id, project_id, version_no)
    except Exception:
        with connect() as conn:
            conn.execute("DELETE FROM versions WHERE project_id = ? AND version_no = ?", (project_id, version_no))
        if os.path.exists(path):
            os.remove(path)
        raise

    return version_no


def delete_latest_version(user_id, project_id, version_no):
    with connect() as conn:
        get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)
        if len(versions) <= 1:
            raise WorkflowError("VERSION_FIRST_NOT_DELETABLE")
        if versions[-1]["version_no"] != version_no:
            raise WorkflowError("VERSION_ONLY_LATEST_DELETABLE")
        path = versions[-1]["file_path"]
        conn.execute("DELETE FROM versions WHERE project_id = ? AND version_no = ?", (project_id, version_no))
        conn.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now_iso(), project_id))
    if path and os.path.exists(path):
        os.remove(path)


def delete_project(user_id, project_id):
    with connect() as conn:
        get_project_row(conn, user_id, project_id)
        conn.execute("DELETE FROM versions WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM llm_calls WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    shutil.rmtree(project_dir(project_id), ignore_errors=True)


def rename_project(user_id, project_id, name):
    name = (name or "").strip()
    if not name:
        raise WorkflowError("PROJECT_NAME_EMPTY")
    with connect() as conn:
        get_project_row(conn, user_id, project_id)
        conn.execute("UPDATE projects SET name = ?, updated_at = ? WHERE id = ?", (name[:120], now_iso(), project_id))


def get_project_detail(user_id, project_id):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)
    return serialize_project(project, versions)


def list_projects(user_id):
    with connect() as conn:
        projects = conn.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC, id DESC", (user_id,)
        ).fetchall()
        return [serialize_project(p, get_versions(conn, p["id"]), include_details=False) for p in projects]



def resolve_settings(project_row, problem_type, target, target_mode):
    if problem_type not in ("classification", "clustering"):
        raise WorkflowError("INVALID_PROBLEM_TYPE")

    config = {"problem_type": problem_type, "target": None, "target_mode": None, "target_type": None}

    if problem_type == "classification":
        target_mode = target_mode or "detected"
        if target_mode not in TARGET_TYPES:
            raise WorkflowError("INVALID_TARGET_MODE")
        config["target_mode"] = target_mode
        config["target_type"] = TARGET_TYPES[target_mode]

        if target_mode == "ai":
            definition = get_draft(project_row).get("ai_definition")
            if not definition:
                raise WorkflowError("PSEUDO_TARGET_MISSING")
            config["ai_definition"] = definition
            config["target"] = AI_TARGET_COLUMN
        else:
            columns = from_json(project_row["columns_json"])
            if not target or target not in columns:
                raise WorkflowError("TARGET_NOT_FOUND")
            config["target"] = target
    else:
        config["target_mode"] = "clustering_fallback" if target_mode == "clustering" else None

    return config


def target_info_from_config(config):
    if config.get("target_type") == "pseudo" or config.get("target_mode") == "ai":
        return {"type": "pseudo", "definition": config["ai_definition"]}
    return {"type": config.get("target_type") or TARGET_TYPES.get(config.get("target_mode"), "observed"),
            "column": config["target"]}


def validate_target(user_id, project_id, target):
    _, df = load_project_dataframe(user_id, project_id)
    if target not in df.columns:
        raise WorkflowError("TARGET_NOT_FOUND")
    classes = df[target].dropna().astype(str).value_counts()
    if len(classes) < 2:
        raise WorkflowError("TARGET_TOO_FEW_CLASSES")
    if classes.min() < 2:
        raise WorkflowError("TARGET_SINGLE_SAMPLE_CLASS", {"classes": classes[classes < 2].index.tolist()[:10]})
    if len(classes) * 2 > len(df):
        raise WorkflowError("TARGET_TOO_MANY_CLASSES", {"classes": len(classes), "rows": len(df)})
    return {"classes": [{"label": str(label), "count": int(count)} for label, count in classes.items()]}


def _first_batch_training_rows(df, batches):
    train, _, _ = batch_split(len(df), batches, None, DEFAULT_TEST_SIZE, DEFAULT_SEED)
    first = batches.min()
    return df.iloc[train[batches[train] == first]]


def generate_ai_target(user_id, project_id, fallback_policy="notify", llm_service=None):


    if fallback_policy not in ("notify", "abort"):
        fallback_policy = "notify"

    project, (df, batches) = load_project_dataframe(user_id, project_id, with_batches=True)
    fit_rows = _first_batch_training_rows(df, batches)

    service = llm_service if llm_service is not None else get_llm_service()
    config = read_config()
    record = {
        "request_id": uuid.uuid4().hex,
        "requested_method": "llm",
        "requested_model": (service.models[0] if service else (config["models"][0] if config["models"] else None)),
        "successful_model": None,
        "actual_method": None,
        "fallback_used": False,
        "fallback_reason": None,
        "fallback_policy": fallback_policy,
        "latency_ms": 0.0,
        "status": "FAILED",
        "attempts": [],
    }

    column_analysis = ColumnAnalyzer(fit_rows).analyze()
    profile = build_prompt_profile(fit_rows, column_analysis)
    numeric_columns = [c for c, info in column_analysis.items() if info["semantic_type"] == "numerical"]
    definition = None
    failure = None

    if service is None:
        failure = "NOT_CONFIGURED"
    else:
        try:
            suggestion, call = service.suggest(profile, numeric_columns, record["request_id"])
            record.update({k: call[k] for k in ("successful_model", "attempts", "latency_ms")})
            definition = new_definition(
                suggestion["features"], source="llm", directions=suggestion["directions"],
                reason={"en": suggestion["reason_en"], "fa": suggestion["reason_fa"],
                        "target_name": suggestion["target_name"],
                        "rejected_features": suggestion["rejected_features"]},
            )
            definition, _ = fit_definition(definition, fit_rows)
            record.update({"actual_method": "llm", "status": "SUCCESS"})
        except LLMTargetServiceError as exc:
            record.update({k: exc.record.get(k, record[k]) for k in ("attempts", "latency_ms")})
            failure = exc.record.get("error_code", "CONNECTION_ERROR")
            definition = None
        except AppError as exc:  # LLM features could not form classes
            failure = "INVALID_COLUMNS" if exc.code == "PSEUDO_TARGET_NO_NUMERIC" else "INVALID_RESPONSE"
            definition = None

    if definition is None:
        record["fallback_reason"] = failure
        if fallback_policy == "abort":
            record.update({"actual_method": None, "status": "FAILED"})
            log_llm_call(user_id, project_id, record)
            code = "LLM_NOT_CONFIGURED" if failure == "NOT_CONFIGURED" else f"LLM_{failure}"
            raise AppError(code, {"request_id": record["request_id"]}, status=503)
        record.update({"actual_method": "statistical", "fallback_used": True, "status": "FALLBACK"})
        definition = build_statistical_definition(fit_rows)
        definition, _ = fit_definition(definition, fit_rows)

    public_record = {k: v for k, v in record.items()}
    definition["llm"] = public_record
    log_llm_call(user_id, project_id, record)

    rule = rule_from_definition(definition)
    labels = rule.transform(df)
    order = rule.fitted["class_labels"]
    counts = labels.value_counts()

    save_draft(project_id, {"ai_definition": definition, "target_mode": "ai"})

    return {
        "target_column": AI_TARGET_COLUMN,
        "target_type": "pseudo",
        "source": definition["source"],
        "classes": [{"label": label, "count": int(counts.get(label, 0))} for label in order],
        "definition": _public_definition(definition),
        "llm": public_record,
        "privacy": profile["privacy"],
        "notice": None if record["status"] == "SUCCESS" else {
            "code": "LLM_FALLBACK_STATISTICAL", "params": {"reason": failure},
        },
    }



def _selection_frame(df, config):
    if config.get("target_type") == "pseudo":
        return df, None
    return df, config["target"]


def get_characteristics(user_id, project_id, problem_type, target, target_mode):
    project, df = load_project_dataframe(user_id, project_id)
    config = resolve_settings(project, problem_type, target, target_mode)
    frame, target_column = _selection_frame(df, config)
    return characteristics_detector.detect(frame, target=target_column)


def _algorithms_for(problem_type, preferences):
    return CLASSIFICATION_ALGORITHMS if problem_type == "classification" else CLUSTERING_ALGORITHMS


def select_models(user_id, project_id, problem_type, target, target_mode, preferences):
    project, df = load_project_dataframe(user_id, project_id)
    config = resolve_settings(project, problem_type, target, target_mode)
    preferences = dict(preferences or {})
    frame, target_column = _selection_frame(df, config)

    response = model_selection_application.run_dataframe(
        frame, problem_type, target_column, preferences, _algorithms_for(problem_type, preferences))

    save_draft(project_id, {"problem_type": problem_type, "target": config["target"],
                            "target_mode": config["target_mode"], "preferences": preferences})
    return response



def _execute(df, batches, config, project_id=None, version_no=None):
    problem_type = config["problem_type"]
    preferences = config.get("preferences") or {}

    if problem_type == "classification":
        result = run_classification(df, config["algorithm"], target_info_from_config(config), batch_ids=batches)
        target_column = config["target"]
    else:
        result = run_clustering(df, config["algorithm"], preferences.get("cluster_count"))
        target_column = None

    result["problem_type"] = problem_type
    result["target"] = target_column
    result["target_type"] = config.get("target_type")
    if config.get("target_type") == "pseudo":
        result["target_source"] = (config.get("ai_definition") or {}).get("source")

    definition = result.pop("fitted_target_definition", None)
    characteristics = characteristics_detector.detect(
        df, target=target_column if problem_type == "classification" and config.get("target_type") != "pseudo" else None)

    result["provenance"] = build_provenance(project_id, version_no, df, result, config, definition)
    return result, characteristics, definition


def build_provenance(project_id, version_no, df, result, config, definition):
    summary = result.get("data_summary", {})
    protocol = result.get("protocol", {})
    target_type = config.get("target_type")
    llm = (definition or config.get("ai_definition") or {}).get("llm") if target_type == "pseudo" else None

    return {
        "project_id": project_id,
        "dataset_version": f"v{version_no}" if version_no else None,
        "dataset_scope": "cumulative_batches_1_to_n",
        "initial_rows": summary.get("rows"),
        "final_rows": summary.get("rows_used"),
        "train_rows": summary.get("train_rows"),
        "test_rows": summary.get("test_rows"),
        "row_drops": summary.get("row_drops", []),
        "features_used": summary.get("input_features"),
        "feature_count": len(summary.get("input_features") or []),
        "encoded_feature_count": summary.get("features"),
        "dropped_columns": summary.get("dropped_column_reasons"),
        "task_type": config["problem_type"],
        "target_column": config.get("target"),
        "target_origin": target_type,
        "target_definition": _public_definition(definition) if definition else None,
        "algorithm": config["algorithm"],
        "hyperparameters": protocol.get("hyperparameters"),
        "split": protocol.get("split"),
        "stratified": protocol.get("stratified"),
        "random_seed": protocol.get("random_seed"),
        "preprocessing": protocol.get("preprocessing"),
        "model_selection_preferences": config.get("preferences"),
        "metrics": _flat_metrics(result.get("metrics", {})),
        "cross_validation": result.get("cross_validation"),
        "latency_ms": result.get("latency_ms"),
        "llm": llm,
        "environment": environment_versions(),
        "generated_at": now_iso(),
    }


def _flat_metrics(metrics):
    return {k: v for k, v in metrics.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}


def _store_result(project_id, version_no, result, characteristics):
    with connect() as conn:
        conn.execute(
            """UPDATE versions SET status = 'completed', result_json = ?, characteristics_json = ?, error = NULL,
                   completed_at = ? WHERE project_id = ? AND version_no = ?""",
            (to_json(result), to_json(characteristics), now_iso(), project_id, version_no),
        )
        conn.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now_iso(), project_id))


def _persist_frozen_definition(project_id, config, definition):
    if not definition or config.get("target_type") != "pseudo":
        return config
    config = dict(config)
    config["ai_definition"] = definition
    with connect() as conn:
        conn.execute("UPDATE projects SET config_json = ? WHERE id = ?", (to_json(config), project_id))
    return config


def run_version(user_id, project_id, version_no):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)
    config = from_json(project["config_json"])
    if not config:
        raise WorkflowError("PROJECT_NOT_CONFIGURED")

    df, batches = load_cumulative_dataframe(project, versions, upto_version_no=version_no, with_batches=True)
    result, characteristics, definition = _execute(df, batches, config, project_id, version_no)
    _persist_frozen_definition(project_id, config, definition)
    _store_result(project_id, version_no, result, characteristics)


def configure_and_run(user_id, project_id, algorithm, problem_type, target, target_mode, preferences):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)

    config = resolve_settings(project, problem_type, target, target_mode)
    preferences = dict(preferences or {})
    available = _algorithms_for(problem_type, preferences)
    if algorithm not in available:
        raise WorkflowError("ALGORITHM_UNKNOWN", {"algorithm": algorithm})

    rows = versions[-1]["total_rows"] if versions else 0
    reason = eligibility(algorithm, problem_type, rows, preferences)
    if reason:
        raise WorkflowError("ALGORITHM_NOT_ALLOWED", {"algorithm": algorithm, "reason": reason})

    config["algorithm"] = algorithm
    config["preferences"] = preferences

    outputs = []
    for version in versions:
        df, batches = load_cumulative_dataframe(project, versions, upto_version_no=version["version_no"],
                                                with_batches=True)
        result, characteristics, definition = _execute(df, batches, config, project_id, version["version_no"])
        if definition is not None and config.get("target_type") == "pseudo":
            config["ai_definition"] = definition  # frozen after the first fit (Option A)
        outputs.append((version["version_no"], result, characteristics))

    with connect() as conn:
        conn.execute("UPDATE projects SET config_json = ?, status = 'ready', updated_at = ? WHERE id = ?",
                     (to_json(config), now_iso(), project_id))

    for version_no, result, characteristics in outputs:
        _store_result(project_id, version_no, result, characteristics)



def audit_record(user_id, project_id, version_no):
    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        row = conn.execute("SELECT * FROM versions WHERE project_id = ? AND version_no = ?",
                           (project_id, version_no)).fetchone()
        calls = conn.execute("SELECT record_json FROM llm_calls WHERE project_id = ? ORDER BY id",
                             (project_id,)).fetchall()
    if row is None or not row["result_json"]:
        raise AppError("PROJECT_NOT_CONFIGURED", status=404)
    result = from_json(row["result_json"])
    return {
        "project": {"id": project["id"], "name": project["name"]},
        "version": {"version_no": row["version_no"], "filename": row["filename"], "rows_added": row["rows_added"],
                    "total_rows": row["total_rows"], "created_at": row["created_at"],
                    "completed_at": row["completed_at"], "issues": from_json(row["issues_json"])},
        "provenance": result.get("provenance"),
        "metrics": result.get("metrics"),
        "ablation": result.get("ablation"),
        "feature_importance": result.get("feature_importance"),
        "data_summary": result.get("data_summary"),
        "llm_call_log": [from_json(c["record_json"]) for c in calls],
    }


def flatten(value, prefix=""):
    rows = []
    if isinstance(value, dict):
        for key, item in value.items():
            rows.extend(flatten(item, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list) and value and all(isinstance(v, (int, float, str, bool)) or v is None for v in value):
        rows.append((prefix, "; ".join("" if v is None else str(v) for v in value)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(flatten(item, f"{prefix}[{index}]"))
    else:
        rows.append((prefix, "" if value is None else value))
    return rows


def audit_csv(record):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value"])
    for key, value in flatten({k: v for k, v in record.items() if k != "feature_importance"}):
        if key.startswith("metrics.cluster_points"):
            continue
        writer.writerow([key, value])
    return buffer.getvalue()


def audit_json(record):
    return json.dumps(record, ensure_ascii=False, indent=2, default=str)
