

import pandas as pd

from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.model_execution.executor import ModelExecutionService
from ml_engine.model_selection.algorithm_registry import (
    CLASSIFICATION_ALGORITHMS,
    CLUSTERING_ALGORITHMS,
)


class ModelRunError(ValueError):
    """A problem the user can act on"""


_execution_service = ModelExecutionService()


def run_model_on_dataframe(df, algorithm, problem_type, target=None, preferences=None):

    preferences = preferences or {}

    if problem_type == "classification":
        registry = CLASSIFICATION_ALGORITHMS
    elif problem_type == "clustering":
        registry = CLUSTERING_ALGORITHMS
    else:
        raise ModelRunError("نوع مسئله پشتیبانی نمی‌شود")

    if algorithm not in registry:
        raise ModelRunError(f"الگوریتم «{algorithm}» برای این نوع تحلیل تعریف نشده است")

    if df is None or df.empty:
        raise ModelRunError("دیتاست خالی است")

    if problem_type == "classification":

        if not target or target not in df.columns:
            raise ModelRunError("ستون نتیجه (Target) در دیتاست پیدا نشد")

        counts = df[target].dropna().astype(str).value_counts()

        if len(counts) < 2:
            raise ModelRunError("ستون نتیجه باید حداقل دو مقدار (کلاس) متفاوت داشته باشد")

    pipeline = PreprocessingPipeline(
        df,
        problem_type,
        target if problem_type == "classification" else None
    )

    processed = pipeline.process()

    X = processed["dataframe"]
    y = processed["target"]

    if X.shape[1] == 0:
        raise ModelRunError("هیچ ستون قابل استفاده‌ای برای تحلیل باقی نماند")

    if problem_type == "classification":

        if y is None:
            raise ModelRunError("ستون نتیجه (Target) مشخص نشده است")

        counts = pd.Series(y).value_counts()

        if len(counts) < 2:
            raise ModelRunError("بعد از پاک‌سازی داده‌ها فقط یک کلاس باقی ماند")

        if counts.min() < 2:
            raise ModelRunError(
                "این Target برای Classification مناسب نیست چون بعضی کلاس‌ها نمونه کافی ندارند"
            )


        if round(len(y) * 0.2) < len(counts):
            raise ModelRunError(
                "تعداد داده‌ها نسبت به تعداد کلاس‌ها خیلی کم است؛ داده بیشتری بارگذاری کنید"
            )

    if problem_type == "clustering":

        if len(X) < 3:
            raise ModelRunError("برای گروه‌بندی حداقل ۳ ردیف داده لازم است")

        cluster_count = preferences.get("cluster_count")

        if cluster_count not in (None, "", 0):

            try:
                cluster_count = int(cluster_count)
            except (TypeError, ValueError):
                raise ModelRunError("تعداد گروه‌ها باید یک عدد صحیح باشد")

            if cluster_count < 2 or cluster_count >= len(X):
                raise ModelRunError(
                    f"تعداد گروه‌ها باید بین ۲ و {len(X) - 1} باشد"
                )

            preferences = {**preferences, "cluster_count": cluster_count}

    result = _execution_service.execute(
        algorithm,
        X,
        y,
        problem_type,
        preferences,
        target_classes=processed["target_classes"]
    )

    result["data_summary"] = {
        "rows": int(len(df)),
        "rows_used": int(len(X)),
        "features": int(X.shape[1]),
        "dropped_columns": [str(c) for c in processed["dropped_columns"]],
    }

    return result
