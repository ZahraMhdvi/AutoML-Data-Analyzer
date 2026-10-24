

import numpy as np
import pandas as pd

from ml_engine.errors import AppError
from ml_engine.preprocessing.pipeline import (
    HIGH_MISSING_RATIO,
    is_identifier_column,
    is_free_text_column,
    mostly_numeric_text_columns,
)


MIN_ROWS_ERROR = 10
MIN_ROWS_WARNING = 30
HIGH_CARDINALITY = 50
IMBALANCE_RATIO = 10.0


def _issue(code, severity, **params):
    clean = {}
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            clean[key] = [str(item) for item in value]
        elif isinstance(value, (np.integer,)):
            clean[key] = int(value)
        elif isinstance(value, (np.floating,)):
            clean[key] = float(value)
        else:
            clean[key] = value
    return {"code": code, "severity": severity, "params": clean}


def validate_dataframe(df, target=None):
    issues = []
    rows = int(len(df))

    if rows < MIN_ROWS_ERROR:
        issues.append(_issue("TOO_FEW_ROWS", "error", rows=rows, min_rows=MIN_ROWS_ERROR))
    elif rows < MIN_ROWS_WARNING:
        issues.append(_issue("SMALL_DATASET", "warning", rows=rows, recommended=MIN_ROWS_WARNING))

    features = df.drop(columns=[target]) if target and target in df.columns else df

    numeric = features.select_dtypes(include="number")
    inf_columns = [c for c in numeric.columns if np.isinf(numeric[c].to_numpy(dtype=float, na_value=np.nan)).any()]
    if inf_columns:
        issues.append(_issue("INFINITE_VALUES", "warning", columns=inf_columns))

    constant = [c for c in features.columns if features[c].nunique(dropna=True) <= 1]
    if constant:
        issues.append(_issue("CONSTANT_COLUMNS", "warning", columns=constant))

    high_null = [c for c in features.columns if 0 < features[c].isna().mean() and features[c].isna().mean() > HIGH_MISSING_RATIO]
    if high_null:
        issues.append(_issue("HIGH_MISSING_COLUMNS", "warning", columns=high_null, threshold=HIGH_MISSING_RATIO))

    mixed = mostly_numeric_text_columns(features)
    really_mixed = [c for c in features.columns if _is_mixed(features[c])]
    if mixed:
        issues.append(_issue("MIXED_TYPES_COERCED", "warning", columns=mixed))
    other_mixed = [c for c in really_mixed if c not in mixed]
    if other_mixed:
        issues.append(_issue("MIXED_TYPES", "warning", columns=other_mixed))

    high_card = [
        c for c in features.columns
        if not pd.api.types.is_numeric_dtype(features[c])
        and features[c].nunique(dropna=True) > HIGH_CARDINALITY
        and not is_identifier_column(features, c)
        and not is_free_text_column(features, c)
    ]
    if high_card:
        issues.append(_issue("HIGH_CARDINALITY", "warning", columns=high_card, max_categories=30))

    duplicates = int(df.duplicated().sum())
    if duplicates:
        issues.append(_issue("DUPLICATE_ROWS", "info", count=duplicates))

    usable = [
        c for c in features.columns
        if c not in constant
        and not is_identifier_column(features, c)
        and not is_free_text_column(features, c)
        and not features[c].isna().all()
        and not pd.api.types.is_datetime64_any_dtype(features[c])
    ]
    if not usable:
        issues.append(_issue("NO_USABLE_FEATURES", "error"))

    if target and target in df.columns:
        issues.extend(validate_target(df[target]))

    return issues


def validate_target(series):
    issues = []
    counts = series.dropna().astype(str).value_counts()
    missing = int(series.isna().sum())

    if missing:
        issues.append(_issue("TARGET_MISSING_ROWS", "warning", count=missing))
    if len(counts) < 2:
        issues.append(_issue("TARGET_TOO_FEW_CLASSES", "error"))
        return issues

    singles = counts[counts < 2].index.tolist()
    if singles:
        issues.append(_issue("TARGET_SINGLE_SAMPLE_CLASS", "error", classes=singles))

    ratio = counts.max() / max(counts.min(), 1)
    if ratio >= IMBALANCE_RATIO:
        issues.append(_issue("IMBALANCED_TARGET", "warning", ratio=round(float(ratio), 1)))

    if len(counts) > 20:
        issues.append(_issue("TARGET_MANY_CLASSES", "warning", classes=int(len(counts))))

    return issues


def _is_mixed(series):
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
        return False
    values = series.dropna()
    if values.empty:
        return False
    kinds = values.map(lambda v: type(v).__name__).value_counts()
    return len(kinds) > 1


def raise_on_errors(issues):
    for issue in issues:
        if issue["severity"] == "error":
            raise AppError(issue["code"], issue["params"])


def schema_changes(expected_columns, frame, expected_dtypes=None):
    missing = [c for c in expected_columns if c not in frame.columns]
    extra = [c for c in frame.columns if c not in expected_columns]
    changed = []
    for column, kind in (expected_dtypes or {}).items():
        if column in frame.columns and _kind(frame[column]) != kind:
            changed.append(column)
    return missing, extra, changed


def _kind(series):
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "text"


def column_kinds(frame):
    return {str(c): _kind(frame[c]) for c in frame.columns}
