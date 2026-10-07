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



def build_statistical_definition(dataframe, max_features=3):


    import numpy as np

    from ml_engine.preprocessing.pipeline import is_identifier_column

    numeric = [
        column
        for column in dataframe.columns
        if pd.api.types.is_numeric_dtype(dataframe[column])
        and not pd.api.types.is_bool_dtype(dataframe[column])
        and not is_identifier_column(dataframe, column)
        and dataframe[column].nunique(dropna=True) > 2
    ]

    if not numeric:
        raise ValueError("برای ساخت Target به حداقل یک ستون عددی نیاز است")

    if len(numeric) == 1:
        chosen = numeric

    else:
        values = dataframe[numeric].astype(float)
        values = values.fillna(values.median())

        std = values.std(ddof=0).replace(0, 1)
        standardized = (values - values.mean()) / std


        _, _, vt = np.linalg.svd(standardized.to_numpy(), full_matrices=False)
        loadings = pd.Series(vt[0], index=numeric)

        dominant_sign = np.sign(loadings[loadings.abs().idxmax()]) or 1.0
        same_direction = loadings[np.sign(loadings) == dominant_sign]

        chosen = (
            same_direction.abs()
            .sort_values(ascending=False)
            .head(max_features)
            .index
            .tolist()
        )

        if len(chosen) < 2:
            chosen = (
                loadings.abs()
                .sort_values(ascending=False)
                .head(min(max_features, len(numeric)))
                .index
                .tolist()
            )

    features_text = "، ".join(chosen)

    return {
        "target_name": "generated_target",
        "classes": LABELS_BY_BIN_COUNT[3],
        "important_features": chosen,
        "reason": (
            f"ستون‌های {features_text} بیشترین تغییرات مشترک را در داده‌ها دارند. "
            "سیستم این ستون‌ها را با هم ترکیب کرد و هر ردیف را بر اساس مجموع آن‌ها "
            "در یکی از سه سطح Low (کم)، Medium (متوسط) و High (زیاد) قرار داد؛ "
            "به این ترتیب گروه‌ها تقریباً هم‌اندازه هستند."
        ),
        "method": "statistical",
    }
