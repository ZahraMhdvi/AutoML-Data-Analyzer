


import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


MISSING_CATEGORY = "__missing__"


class MissingHandler(BaseEstimator, TransformerMixin):

    def __init__(self, dataframe=None):

        self.dataframe = dataframe



    def fit(self, X, y=None):
        self.fill_values_ = {}
        self.strategy_ = {}

        for column in X.columns:
            series = X[column]

            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                median = series.median()
                self.fill_values_[column] = 0.0 if pd.isna(median) else float(median)
                self.strategy_[column] = "median"
            else:
                mode = series.dropna().mode()
                self.fill_values_[column] = mode.iloc[0] if len(mode) else MISSING_CATEGORY
                self.strategy_[column] = "mode"

        self.n_missing_train_ = {column: int(X[column].isna().sum()) for column in X.columns}
        return self


    def transform(self, X):
        df = X.copy()

        for column, value in self.fill_values_.items():
            if column in df.columns and df[column].isna().any():
                df[column] = df[column].fillna(value)

        return df

    def get_params_report(self):
        return {
            column: {"strategy": self.strategy_[column], "value": _jsonable(value)}
            for column, value in self.fill_values_.items()
        }



    def get_missing_report(self):
        return self.dataframe.isnull().sum().to_dict()

    def fill_missing(self):

        return self.fit(self.dataframe).transform(self.dataframe)


def _jsonable(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value if isinstance(value, (int, float, str, bool)) or value is None else str(value)
