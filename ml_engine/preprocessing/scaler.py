
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureScaler(BaseEstimator, TransformerMixin):

    def __init__(self, dataframe=None, numeric_columns=None):
        self.dataframe = dataframe
        self.numeric_columns = numeric_columns

    def fit(self, X, y=None):
        columns = self.numeric_columns
        if columns is None:
            columns = [
                column for column in X.columns
                if pd.api.types.is_numeric_dtype(X[column]) and not pd.api.types.is_bool_dtype(X[column])
            ]
        self.columns_ = [column for column in columns if column in X.columns]

        values = X[self.columns_].astype(float)
        self.mean_ = values.mean().to_dict()
        std = values.std(ddof=0).replace(0, 1.0).fillna(1.0)
        self.scale_ = std.to_dict()
        return self

    def transform(self, X):
        df = X.copy()
        for column in self.columns_:
            if column in df.columns:
                df[column] = (df[column].astype(float) - self.mean_[column]) / self.scale_[column]
        return df

    def get_params_report(self):
        return {
            column: {"mean": _round(self.mean_[column]), "scale": _round(self.scale_[column])}
            for column in self.columns_
        }


    def scale(self):
        return self.fit(self.dataframe).transform(self.dataframe)


def _round(value):
    value = float(value)
    return None if np.isnan(value) else round(value, 6)
