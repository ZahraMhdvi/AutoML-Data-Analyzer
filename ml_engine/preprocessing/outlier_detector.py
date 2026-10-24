


import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


POLICIES = ("none", "clip")


class OutlierDetector(BaseEstimator, TransformerMixin):

    def __init__(self, dataframe=None, policy="none", factor=1.5):
        self.dataframe = dataframe
        self.policy = policy
        self.factor = factor

    def get_numeric_columns(self, frame=None):
        frame = self.dataframe if frame is None else frame
        return [
            column for column in frame.columns
            if pd.api.types.is_numeric_dtype(frame[column]) and not pd.api.types.is_bool_dtype(frame[column])
        ]

    def fit(self, X, y=None):
        if self.policy not in POLICIES:
            raise ValueError(f"Unknown outlier policy: {self.policy}")

        self.bounds_ = {}
        self.train_outliers_ = {}

        for column in self.get_numeric_columns(X):
            series = X[column].astype(float)
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                continue
            lower, upper = q1 - self.factor * iqr, q3 + self.factor * iqr
            self.bounds_[column] = (float(lower), float(upper))
            self.train_outliers_[column] = int(((series < lower) | (series > upper)).sum())

        return self

    def transform(self, X):
        if self.policy == "none":
            return X
        df = X.copy()
        for column, (lower, upper) in self.bounds_.items():
            if column in df.columns:
                df[column] = df[column].astype(float).clip(lower, upper)
        return df

    def get_params_report(self):
        return {
            "policy": self.policy,
            "factor": self.factor,
            "train_outlier_counts": self.train_outliers_,
            "bounds": {column: [round(a, 6), round(b, 6)] for column, (a, b) in self.bounds_.items()},
        }


    def detect_outliers(self):
        self.fit(self.dataframe)
        return {column: self.train_outliers_.get(column, 0) for column in self.get_numeric_columns()}
