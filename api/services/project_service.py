

import logging
import os
import shutil

import pandas as pd
from fastapi import HTTPException

from api.core.db import (
    connect,
    now_iso,
    project_dir,
    to_json,
    from_json,
)
from api.core.datasets import read_dataset_file, check_extension
from ml_engine.analysis.application.analysis_application import AnalysisApplication
from ml_engine.ai.target_generator import TargetGenerator, build_statistical_definition
from ml_engine.ai.llm_target_service import LLMTargetServiceError
from ml_engine.model_execution.runner import run_model_on_dataframe
from ml_engine.model_selection.application.model_selection_application import (
    ModelSelectionApplication,
)
from ml_engine.model_selection.algorithm_registry import (
    CLASSIFICATION_ALGORITHMS,
    CLUSTERING_ALGORITHMS,
)
from ml_engine.model_selection.data_characteristics import DataCharacteristicsDetector


AI_TARGET_COLUMN = "generated_target"

logger = logging.getLogger(__name__)

analysis_application = AnalysisApplication()
model_selection_application = ModelSelectionApplication()
target_generator = TargetGenerator()
characteristics_detector = DataCharacteristicsDetector()


class WorkflowError(ValueError):
    """A user-facing problem with the request (HTTP 400)."""



def get_project_row(conn, user_id, project_id):

    row = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, user_id)
    ).fetchone()

    if row is None:
        raise HTTPException(404, "پروژه پیدا نشد")

    return row


def get_versions(conn, project_id):

    return conn.execute(
        "SELECT * FROM versions WHERE project_id = ? ORDER BY version_no",
        (project_id,)
    ).fetchall()


def load_cumulative_dataframe(project_row, versions, upto_version_no=None):

    columns = from_json(project_row["columns_json"])

    frames = []

    for version in versions:

        if upto_version_no is not None and version["version_no"] > upto_version_no:
            break

        frame = read_dataset_file(version["file_path"])
        frames.append(frame[columns])

    if not frames:
        raise WorkflowError("هیچ داده‌ای برای این پروژه ثبت نشده است")

    return pd.concat(frames, ignore_index=True)


def build_working_dataframe(df, config):


    if config and config.get("target_mode") == "ai":

        definition = config.get("ai_definition")

        if not definition:
            raise WorkflowError("تعریف Target هوشمند پیدا نشد؛ دوباره Target را بسازید")

        return target_generator.generate(df, definition)

    return df



def _main_metrics(result):

    if not result:
        return None

    metrics = result.get("metrics") or {}

    if result.get("problem_type") == "clustering" or "cluster_count" in metrics:
        return {
            "cluster_count": metrics.get("cluster_count"),
            "silhouette_score": metrics.get("silhouette_score"),
            "noise_points": metrics.get("noise_points"),
        }

    return {
        "accuracy": metrics.get("accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
    }


def serialize_version(row, include_result=True):

    result = from_json(row["result_json"])

    data = {
        "version_no": row["version_no"],
        "filename": row["filename"],
        "rows_added": row["rows_added"],
        "total_rows": row["total_rows"],
        "status": row["status"],
        "error": row["error"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "summary": _main_metrics(result),
        "characteristics": from_json(row["characteristics_json"]),
    }

    if include_result:
        data["result"] = result

    return data


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
        "latest_summary": (
            _main_metrics(from_json(completed[-1]["result_json"]))
            if completed else None
        ),
    }

    if include_details:
        data["analysis"] = from_json(row["analysis_json"])
        data["draft"] = from_json(row["draft_json"]) or {}
        data["versions"] = [serialize_version(v) for v in versions]

    return data


def _public_config(config):

    if not config:
        return None

    public = dict(config)

    definition = public.pop("ai_definition", None)

    if definition:
        public["ai_target"] = {
            "important_features": definition.get("important_features"),
            "reason": definition.get("reason"),
            "method": definition.get("method", "ai"),
        }

    return public



def save_batch_file(project_id, version_no, content, filename):

    ext = check_extension(filename)

    path = os.path.join(project_dir(project_id), f"batch_{version_no}{ext}")

    with open(path, "wb") as handle:
        handle.write(content)

    return path


def create_project(user_id, name, filename, content, dataframe):

    analysis = analysis_application.analyze_dataframe(dataframe)

    timestamp = now_iso()

    with connect() as conn:

        cursor = conn.execute(
            """
            INSERT INTO projects (user_id, name, status, columns_json, analysis_json, created_at, updated_at)
            VALUES (?, ?, 'draft', ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                to_json(list(dataframe.columns)),
                to_json(analysis),
                timestamp,
                timestamp,
            )
        )

        project_id = cursor.lastrowid

        try:
            path = save_batch_file(project_id, 1, content, filename)
        except Exception:
            shutil.rmtree(project_dir(project_id), ignore_errors=True)
            raise

        conn.execute(
            """
            INSERT INTO versions (project_id, version_no, filename, file_path, rows_added, total_rows, status, created_at)
            VALUES (?, 1, ?, ?, ?, ?, 'pending', ?)
            """,
            (project_id, filename, path, len(dataframe), len(dataframe), timestamp)
        )

    return project_id


def check_batch_schema(project_row, dataframe):

    expected = from_json(project_row["columns_json"])

    missing = [column for column in expected if column not in dataframe.columns]
    extra = [column for column in dataframe.columns if column not in expected]

    if missing or extra:

        parts = []

        if missing:
            parts.append("ستون‌های جاافتاده: " + "، ".join(missing))

        if extra:
            parts.append("ستون‌های اضافه: " + "، ".join(extra))

        raise WorkflowError(
            "ستون‌های فایل جدید با دیتاست این پروژه یکسان نیست. "
            "اگر این یک دیتاست متفاوت است، آن را به‌صورت «پروژه جدید» بارگذاری کنید. "
            + " | ".join(parts)
        )


def add_version(user_id, project_id, filename, content, dataframe):

    with connect() as conn:

        project = get_project_row(conn, user_id, project_id)

        if project["status"] != "ready":
            raise WorkflowError(
                "ابتدا تحلیل اولیه این پروژه را کامل کنید، سپس داده جدید اضافه کنید"
            )

        check_batch_schema(project, dataframe)

        versions = get_versions(conn, project_id)

        version_no = versions[-1]["version_no"] + 1
        total_rows = versions[-1]["total_rows"] + len(dataframe)

        path = save_batch_file(project_id, version_no, content, filename)

        conn.execute(
            """
            INSERT INTO versions (project_id, version_no, filename, file_path, rows_added, total_rows, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (project_id, version_no, filename, path, len(dataframe), total_rows, now_iso())
        )

    try:
        run_version(user_id, project_id, version_no)

    except Exception:


        with connect() as conn:
            conn.execute(
                "DELETE FROM versions WHERE project_id = ? AND version_no = ?",
                (project_id, version_no)
            )

        if os.path.exists(path):
            os.remove(path)

        raise

    return version_no


def delete_latest_version(user_id, project_id, version_no):

    with connect() as conn:

        get_project_row(conn, user_id, project_id)

        versions = get_versions(conn, project_id)

        if len(versions) <= 1:
            raise WorkflowError("نسخه اول پروژه قابل حذف نیست؛ در صورت نیاز کل پروژه را حذف کنید")

        if versions[-1]["version_no"] != version_no:
            raise WorkflowError("فقط آخرین نسخه قابل حذف است")

        path = versions[-1]["file_path"]

        conn.execute(
            "DELETE FROM versions WHERE project_id = ? AND version_no = ?",
            (project_id, version_no)
        )

        conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now_iso(), project_id)
        )

    if path and os.path.exists(path):
        os.remove(path)


def delete_project(user_id, project_id):

    with connect() as conn:

        get_project_row(conn, user_id, project_id)

        conn.execute("DELETE FROM versions WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    shutil.rmtree(project_dir(project_id), ignore_errors=True)




def load_project_dataframe(user_id, project_id):

    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)

    return project, load_cumulative_dataframe(project, versions)


def save_draft(project_id, updates):

    with connect() as conn:

        row = conn.execute("SELECT draft_json FROM projects WHERE id = ?", (project_id,)).fetchone()

        draft = from_json(row["draft_json"]) or {}
        draft.update(updates)

        conn.execute(
            "UPDATE projects SET draft_json = ?, updated_at = ? WHERE id = ?",
            (to_json(draft), now_iso(), project_id)
        )

    return draft


def get_draft(project_row):
    return from_json(project_row["draft_json"]) or {}


def resolve_settings(project_row, problem_type, target, target_mode):


    if problem_type not in ("classification", "clustering"):
        raise WorkflowError("نوع تحلیل نامعتبر است")

    config = {
        "problem_type": problem_type,
        "target": None,
        "target_mode": None,
    }

    if problem_type == "classification":

        target_mode = target_mode or "detected"

        if target_mode not in ("detected", "manual", "ai"):
            raise WorkflowError("روش انتخاب Target نامعتبر است")

        config["target_mode"] = target_mode

        if target_mode == "ai":

            definition = get_draft(project_row).get("ai_definition")

            if not definition:
                raise WorkflowError("ابتدا Target هوشمند را بسازید")

            config["ai_definition"] = definition
            config["target"] = AI_TARGET_COLUMN

        else:

            columns = from_json(project_row["columns_json"])

            if not target or target not in columns:
                raise WorkflowError("ستون نتیجه (Target) انتخاب نشده یا در دیتاست وجود ندارد")

            config["target"] = target

    else:


        config["target_mode"] = "clustering_fallback" if target_mode == "clustering" else None

    return config


def validate_target(user_id, project_id, target):

    project, df = load_project_dataframe(user_id, project_id)

    if target not in df.columns:
        raise WorkflowError("Target پیدا نشد")

    classes = df[target].dropna().astype(str).value_counts()

    if len(classes) < 2:
        raise WorkflowError("Target باید حداقل دو کلاس داشته باشد")

    if classes.min() < 2:
        raise WorkflowError(
            "بعضی کلاس‌های این Target فقط یک نمونه دارند و برای Classification مناسب نیستند"
        )

    return {
        "classes": [
            {"label": str(label), "count": int(count)}
            for label, count in classes.items()
        ]
    }


def get_characteristics(user_id, project_id, problem_type, target, target_mode):

    project, df = load_project_dataframe(user_id, project_id)

    config = resolve_settings(project, problem_type, target, target_mode)

    working = build_working_dataframe(df, config)

    return characteristics_detector.detect(working, target=config["target"])


def _statistical_definition(df):

    try:
        return build_statistical_definition(df)
    except ValueError:
        raise WorkflowError(
            "ساخت Target برای این دیتاست ممکن نشد چون ستون عددی مناسبی ندارد. "
            "یکی از گزینه‌های دیگر (انتخاب دستی یا گروه‌بندی) را انتخاب کنید."
        )


def generate_ai_target(user_id, project_id, llm_service, profile_builder):


    project, df = load_project_dataframe(user_id, project_id)

    notice = None

    if llm_service is None:

        definition = _statistical_definition(df)
        notice = (
            "سرویس هوش مصنوعی پیکربندی نشده است (کلید OPENROUTER_API_KEY در فایل .env نیست)؛ "
            "به‌جای آن، Target با یک روش آماری از روی داده‌ها ساخته شد."
        )

    else:

        try:
            definition = llm_service.generate_target_definition(profile_builder(df))

        except LLMTargetServiceError as exc:

            logger.warning(
                "AI target generation failed, using statistical fallback: %s",
                " | ".join(getattr(exc, "details", []) or [str(exc)])
            )

            definition = _statistical_definition(df)
            notice = (
                "در حال حاضر مدل‌های هوش مصنوعی پاسخ ندادند؛ "
                "به‌جای آن، Target با یک روش آماری از روی داده‌ها ساخته شد. "
                "می‌توانید ادامه دهید یا کمی بعد «تلاش دوباره» را بزنید."
            )

    try:
        generated = target_generator.generate(df, definition)

    except ValueError:

        if definition.get("method") == "statistical":
            raise WorkflowError(
                "ساخت Target برای این دیتاست ممکن نشد؛ داده‌ها تنوع کافی ندارند. "
                "یکی از گزینه‌های دیگر (انتخاب دستی یا گروه‌بندی) را انتخاب کنید."
            )


        definition = _statistical_definition(df)
        generated = target_generator.generate(df, definition)
        notice = (
            "ستون‌هایی که هوش مصنوعی پیشنهاد داد برای ساخت گروه‌ها مناسب نبودند؛ "
            "Target با یک روش آماری از روی داده‌ها ساخته شد."
        )

    counts = generated[AI_TARGET_COLUMN].value_counts()

    level_order = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
    counts = counts.loc[sorted(counts.index, key=lambda label: (level_order.get(str(label), 99), str(label)))]

    save_draft(project_id, {"ai_definition": definition, "target_mode": "ai"})

    return {
        "target_column": AI_TARGET_COLUMN,
        "classes": [
            {"label": str(label), "count": int(count)}
            for label, count in counts.items()
        ],
        "important_features": definition.get("important_features", []),
        "reason": definition.get("reason", ""),
        "method": definition.get("method", "ai"),
        "notice": notice,
    }


def _algorithms_for(problem_type, preferences):

    if problem_type == "classification":
        return CLASSIFICATION_ALGORITHMS

    algorithms = CLUSTERING_ALGORITHMS

    if preferences.get("cluster_count_known"):
        algorithms = {
            name: config
            for name, config in algorithms.items()
            if name != "DBSCAN"
        }

    return algorithms


def select_models(user_id, project_id, problem_type, target, target_mode, preferences):

    project, df = load_project_dataframe(user_id, project_id)

    config = resolve_settings(project, problem_type, target, target_mode)

    preferences = dict(preferences or {})

    working = build_working_dataframe(df, config)

    response = model_selection_application.run_dataframe(
        working,
        problem_type,
        config["target"],
        preferences,
        _algorithms_for(problem_type, preferences)
    )

    save_draft(project_id, {
        "problem_type": problem_type,
        "target": config["target"],
        "target_mode": config["target_mode"],
        "preferences": preferences,
    })

    return response




def _execute(df, config):

    working = build_working_dataframe(df, config)

    result = run_model_on_dataframe(
        working,
        config["algorithm"],
        config["problem_type"],
        config["target"],
        config.get("preferences") or {}
    )

    result["problem_type"] = config["problem_type"]
    result["target"] = config["target"]


    report = dict(result.get("report") or {})
    report.pop("metrics", None)
    result["report"] = report

    characteristics = characteristics_detector.detect(
        working,
        target=config["target"] if config["problem_type"] == "classification" else None,
    )

    return result, characteristics


def _store_result(project_id, version_no, result, characteristics):

    with connect() as conn:

        conn.execute(
            """
            UPDATE versions
               SET status = 'completed', result_json = ?, characteristics_json = ?,
                   error = NULL, completed_at = ?
             WHERE project_id = ? AND version_no = ?
            """,
            (to_json(result), to_json(characteristics), now_iso(), project_id, version_no)
        )

        conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now_iso(), project_id)
        )


def run_version(user_id, project_id, version_no):

    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)

    config = from_json(project["config_json"])

    if not config:
        raise WorkflowError("تنظیمات تحلیل این پروژه هنوز کامل نشده است")

    df = load_cumulative_dataframe(project, versions, upto_version_no=version_no)

    result, characteristics = _execute(df, config)

    _store_result(project_id, version_no, result, characteristics)


def configure_and_run(user_id, project_id, algorithm, problem_type, target, target_mode, preferences):


    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)

    config = resolve_settings(project, problem_type, target, target_mode)

    preferences = dict(preferences or {})

    available = _algorithms_for(problem_type, preferences)

    if algorithm not in available:
        raise WorkflowError("الگوریتم انتخاب‌شده برای این تنظیمات مجاز نیست")

    config["algorithm"] = algorithm
    config["preferences"] = preferences

    outputs = []

    for version in versions:

        df = load_cumulative_dataframe(project, versions, upto_version_no=version["version_no"])

        outputs.append((version["version_no"],) + _execute(df, config))

    with connect() as conn:

        conn.execute(
            "UPDATE projects SET config_json = ?, status = 'ready', updated_at = ? WHERE id = ?",
            (to_json(config), now_iso(), project_id)
        )

    for version_no, result, characteristics in outputs:
        _store_result(project_id, version_no, result, characteristics)


def get_project_detail(user_id, project_id):

    with connect() as conn:
        project = get_project_row(conn, user_id, project_id)
        versions = get_versions(conn, project_id)

    return serialize_project(project, versions)


def list_projects(user_id):

    with connect() as conn:

        projects = conn.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
            (user_id,)
        ).fetchall()

        items = []

        for project in projects:
            versions = get_versions(conn, project["id"])
            items.append(serialize_project(project, versions, include_details=False))

    return items


def rename_project(user_id, project_id, name):

    name = (name or "").strip()

    if not name:
        raise WorkflowError("نام پروژه نمی‌تواند خالی باشد")

    with connect() as conn:

        get_project_row(conn, user_id, project_id)

        conn.execute(
            "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
            (name[:120], now_iso(), project_id)
        )
