import pandas as pd

LABELS_BY_BIN_COUNT = {
    2: ["Low", "High"],
    3: ["Low", "Medium", "High"],
    4: ["Low", "Medium", "High", "Very High"],
}


class TargetGenerator:

    def generate(self, dataframe, definition):
        features = [
            feature
            for feature in definition.get("important_features", [])
            if feature in dataframe.columns
        ]

        if len(features) == 0:
            raise ValueError("No valid features selected for target generation")

        numeric_features = [
            feature
            for feature in features
            if pd.api.types.is_numeric_dtype(dataframe[feature])
        ]

        score_source = dataframe[numeric_features] if numeric_features else dataframe[features]

        score = score_source.rank(numeric_only=False).mean(axis=1)

        if score.nunique() < 2:
            raise ValueError(
                "Selected features do not have enough variation to build a target"
            )

        for bin_count in (3, 2):
            try:
                target = pd.qcut(
                    score,
                    q=bin_count,
                    labels=LABELS_BY_BIN_COUNT[bin_count],
                    duplicates="drop",
                )

                if target.nunique() >= 2:
                    dataframe = dataframe.copy()
                    dataframe["generated_target"] = target.astype(str)
                    return dataframe

            except ValueError:
                continue

        raise ValueError(
            "Could not build a balanced target from the selected features"
        )
