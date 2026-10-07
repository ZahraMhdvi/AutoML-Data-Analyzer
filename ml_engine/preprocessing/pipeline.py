import re

import pandas as pd
from sklearn.preprocessing import LabelEncoder

from ml_engine.preprocessing.missing_handler import MissingHandler
from ml_engine.preprocessing.outlier_detector import OutlierDetector
from ml_engine.preprocessing.encoder import CategoricalEncoder
from ml_engine.preprocessing.scaler import FeatureScaler


IDENTIFIER_TOKENS = {"id", "uuid", "guid"}

MAX_OUTLIER_DROP_RATIO = 0.25


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


class PreprocessingPipeline:

    def __init__(
            self,
            dataframe,
            problem_type,
            target=None
    ):

        self.dataframe = dataframe

        self.problem_type = problem_type

        self.target = target

        self.target_classes = None

        self.dropped_columns = []

    def _drop_unusable_columns(self, df):

        to_drop = []

        for column in df.columns:

            series = df[column]

            if pd.api.types.is_datetime64_any_dtype(series):
                to_drop.append(column)

            elif is_identifier_column(df, column):
                to_drop.append(column)

            elif is_free_text_column(df, column):
                to_drop.append(column)

            elif series.isna().all():
                to_drop.append(column)

        self.dropped_columns = to_drop

        return df.drop(columns=to_drop) if to_drop else df

    def process(self):

        df = self.dataframe.copy()

        target_column = None

        if self.problem_type == "classification":

            if self.target in df.columns:

                df = df[df[self.target].notna()]

                raw_target = df[self.target].astype(str)

                df = df.drop(
                    columns=[self.target]
                )

                target_column = pd.Series(
                    raw_target.values,
                    index=df.index
                )

        df = self._drop_unusable_columns(df)

        missing_handler = MissingHandler(df)

        df = missing_handler.fill_missing()

        if self.problem_type == "classification":

            outlier_detector = OutlierDetector(df)

            filtered = outlier_detector.remove_outliers()

            if len(filtered) >= len(df) * (1 - MAX_OUTLIER_DROP_RATIO):
                df = filtered

            if target_column is not None:
                target_column = target_column.loc[df.index]

        if target_column is not None:


            encoder = LabelEncoder()

            encoded = encoder.fit_transform(target_column.values)

            self.target_classes = [
                str(value)
                for value in encoder.classes_
            ]

            target_column = encoded

        encoder = CategoricalEncoder(df)

        df = encoder.encode()

        numeric_columns = list(
            df.select_dtypes(
                include=[
                    "int64",
                    "float64",
                    "int32",
                    "float32"
                ]
            ).columns
        )

        if numeric_columns:

            scaler = FeatureScaler(
                df,
                numeric_columns
            )

            df = scaler.scale()

        bool_columns = list(df.select_dtypes(include=["bool"]).columns)

        if bool_columns:
            df[bool_columns] = df[bool_columns].astype(int)

        df.columns = [str(column) for column in df.columns]

        return {

            "dataframe": df,

            "target": target_column,

            "target_classes": self.target_classes,

            "dropped_columns": self.dropped_columns

        }
