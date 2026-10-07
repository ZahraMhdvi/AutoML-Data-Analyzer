

import pandas as pd

from ml_engine.preprocessing.pipeline import (
    is_identifier_column,
    is_free_text_column,
)


NOISE_ROW_RATIO_THRESHOLD = 0.05

MISSING_CELL_RATIO_THRESHOLD = 0.10

HIGH_DIMENSION_MIN_FEATURES = 50
HIGH_DIMENSION_FEATURE_ROW_RATIO = 0.1


class DataCharacteristicsDetector:

    def detect(self, dataframe, target=None, encoded_feature_count=None):

        df = dataframe.copy()

        if target and target in df.columns:
            df = df.drop(columns=[target])

        feature_columns = [
            column
            for column in df.columns
            if not is_identifier_column(df, column)
            and not is_free_text_column(df, column)
            and not pd.api.types.is_datetime64_any_dtype(df[column])
        ]

        features = df[feature_columns]
        rows = int(len(features))

        noise = self._detect_noise(features)
        dimension = self._detect_dimension(features, rows, encoded_feature_count)

        return {
            "rows": rows,
            "noise": noise,
            "dimension": dimension,
            "noise_presence": "has_noise" if noise["has_noise"] else "no_noise",
            "feature_dimension": (
                "high_dimension" if dimension["high_dimension"] else "normal_dimension"
            ),
        }

    def _detect_noise(self, features):

        rows = len(features)

        numeric = features.select_dtypes(include="number")

        outlier_mask = pd.Series(False, index=features.index)
        outlier_columns = []

        for column in numeric.columns:

            series = numeric[column]

            if series.nunique(dropna=True) < 3:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            column_mask = (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)

            if column_mask.any():
                outlier_columns.append(str(column))

            outlier_mask |= column_mask.fillna(False)

        outlier_rows = int(outlier_mask.sum())
        outlier_ratio = outlier_rows / rows if rows else 0.0

        total_cells = features.shape[0] * features.shape[1]
        missing_cells = int(features.isna().sum().sum())
        missing_ratio = missing_cells / total_cells if total_cells else 0.0

        has_noise = (
            outlier_ratio >= NOISE_ROW_RATIO_THRESHOLD
            or missing_ratio >= MISSING_CELL_RATIO_THRESHOLD
        )

        return {
            "has_noise": bool(has_noise),
            "outlier_rows": outlier_rows,
            "outlier_ratio": round(outlier_ratio, 4),
            "outlier_columns": outlier_columns,
            "missing_ratio": round(missing_ratio, 4),
        }

    def _detect_dimension(self, features, rows, encoded_feature_count=None):

        if encoded_feature_count is None:
            encoded_feature_count = self._estimate_encoded_count(features)

        ratio = encoded_feature_count / rows if rows else 0.0

        high_dimension = (
            encoded_feature_count >= HIGH_DIMENSION_MIN_FEATURES
            or ratio >= HIGH_DIMENSION_FEATURE_ROW_RATIO
        )

        return {
            "high_dimension": bool(high_dimension),
            "feature_count": int(features.shape[1]),
            "encoded_feature_count": int(encoded_feature_count),
            "feature_row_ratio": round(ratio, 4),
        }

    @staticmethod
    def _estimate_encoded_count(features):

        count = 0

        for column in features.columns:

            series = features[column]

            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
                count += 1
            else:
                unique = series.nunique(dropna=True)
                count += 1 if unique <= 2 else unique

        return count
