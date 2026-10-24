

import re

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from ml_engine.preprocessing.encoder import CategoricalEncoder
from ml_engine.preprocessing.missing_handler import MissingHandler
from ml_engine.preprocessing.outlier_detector import OutlierDetector
from ml_engine.preprocessing.scaler import FeatureScaler


IDENTIFIER_TOKENS = {"id", "uuid", "guid"}

HIGH_MISSING_RATIO = 0.6
NUMERIC_COERCE_RATIO = 0.95


def _name_tokens(column):
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(column))
    return [token.lower() for token in re.split(r"[^A-Za-z0-9]+", text) if token]


def is_identifier_column(dataframe, column):



    if any(token in IDENTIFIER_TOKENS for token in _name_tokens(column)):
        return True

    series = dataframe[column]
    rows = len(series)

    if rows >= 20 and not pd.api.types.is_numeric_dtype(series):
        if series.nunique(dropna=True) / rows > 0.95:
            return True

    return False


def is_free_text_column(dataframe, column):

    series = dataframe[column]

    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
        return False

    unique_count = series.nunique(dropna=True)

    return unique_count > 50 and unique_count / max(len(series), 1) > 0.5


def sanitize_frame(frame, numeric_columns=None):


    df = frame.copy()

    numeric = df.select_dtypes(include="number").columns
    if len(numeric):
        df[numeric] = df[numeric].replace([np.inf, -np.inf], np.nan)

    for column in numeric_columns or []:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def mostly_numeric_text_columns(frame, ratio=NUMERIC_COERCE_RATIO):


    columns = []
    for column in frame.columns:
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            continue
        values = series.dropna()
        if values.empty:
            continue
        parsed = pd.to_numeric(values.astype(str).str.strip(), errors="coerce")
        if parsed.notna().mean() >= ratio:
            columns.append(column)
    return columns


class ColumnSelector(BaseEstimator, TransformerMixin):



    def fit(self, X, y=None):
        self.dropped_ = {}

        for column in X.columns:
            series = X[column]
            reason = None

            if series.isna().all():
                reason = "ALL_MISSING"
            elif pd.api.types.is_datetime64_any_dtype(series):
                reason = "DATETIME"
            elif is_identifier_column(X, column):
                reason = "IDENTIFIER"
            elif is_free_text_column(X, column):
                reason = "FREE_TEXT"
            elif series.nunique(dropna=True) <= 1:
                reason = "CONSTANT"
            elif series.isna().mean() > HIGH_MISSING_RATIO:
                reason = "HIGH_MISSING"

            if reason:
                self.dropped_[column] = reason

        self.kept_ = [column for column in X.columns if column not in self.dropped_]
        return self

    def transform(self, X):
        return X.reindex(columns=self.kept_)


class PreprocessingPipeline(BaseEstimator, TransformerMixin):



    def __init__(self, problem_type="classification", target=None, outlier_policy="none",
                 scale=True, max_categories=30):
        self.problem_type = problem_type
        self.target = target
        self.outlier_policy = outlier_policy
        self.scale = scale
        self.max_categories = max_categories



    def fit(self, X, y=None):
        X = self._features(X)

        self.input_columns_ = list(X.columns)
        self.coerced_numeric_ = mostly_numeric_text_columns(X)

        frame = sanitize_frame(X, self.coerced_numeric_)

        self.selector_ = ColumnSelector().fit(frame)
        frame = self.selector_.transform(frame)

        self.imputer_ = MissingHandler().fit(frame)
        frame = self.imputer_.transform(frame)

        self.outliers_ = OutlierDetector(policy=self.outlier_policy).fit(frame)
        frame = self.outliers_.transform(frame)

        self.encoder_ = CategoricalEncoder(max_categories=self.max_categories).fit(frame)
        frame = self.encoder_.transform(frame)
        frame = self._to_numeric(frame)

        self.scaler_ = FeatureScaler().fit(frame) if self.scale else None

        self.feature_names_ = [str(column) for column in frame.columns]
        self.n_train_rows_ = int(len(X))
        return self



    def transform(self, X):
        X = self._features(X).reindex(columns=self.input_columns_)

        frame = sanitize_frame(X, self.coerced_numeric_)
        frame = self.selector_.transform(frame)
        frame = self.imputer_.transform(frame)
        frame = self.outliers_.transform(frame)
        frame = self.encoder_.transform(frame)
        frame = self._to_numeric(frame)

        if self.scaler_ is not None:
            frame = self.scaler_.transform(frame)

        frame.columns = [str(column) for column in frame.columns]
        return frame.astype(float)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_, dtype=object)


    def _features(self, X):
        if self.target and self.target in X.columns:
            return X.drop(columns=[self.target])
        return X

    @staticmethod
    def _to_numeric(frame):
        bools = frame.select_dtypes(include=["bool"]).columns
        if len(bools):
            frame[bools] = frame[bools].astype(int)
        return frame

    @property
    def dropped_columns(self):
        return list(self.selector_.dropped_)

    def report(self):



        return {
            "fitted_on_rows": self.n_train_rows_,
            "dropped_columns": [
                {"column": str(column), "reason": reason}
                for column, reason in self.selector_.dropped_.items()
            ],
            "coerced_numeric_columns": [str(column) for column in self.coerced_numeric_],
            "imputation": self.imputer_.get_params_report(),
            "outliers": self.outliers_.get_params_report(),
            "encoding": self.encoder_.get_params_report(),
            "unseen_categories": dict(getattr(self.encoder_, "unseen_counts_", {}) or {}),
            "scaling": self.scaler_.get_params_report() if self.scaler_ is not None else None,
            "output_features": list(self.feature_names_),
        }



    def process(self, dataframe):


        features = self.fit(dataframe).transform(dataframe)
        return {"dataframe": features, "dropped_columns": self.dropped_columns}
