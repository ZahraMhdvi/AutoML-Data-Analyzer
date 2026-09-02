from ml_engine.model_selection.scoring_config import (
    CLASSIFICATION_SCORING_CONFIG,
    CLUSTERING_SCORING_CONFIG
)

class DatasetFeatureAnalyzer:

    def analyze(self, context):

        if context.problem_type == "classification":
            config = CLASSIFICATION_SCORING_CONFIG

        elif context.problem_type == "clustering":
            config = CLUSTERING_SCORING_CONFIG


        else:

            return {}



        features = {}

        rows = context.clean_data_shape["rows"]
        columns = context.clean_data_shape["columns"]
        thresholds = config["thresholds"]
        features["small_dataset"] = (rows < thresholds["small_dataset_max_rows"])
        features["large_dataset"] = (rows > thresholds["large_dataset_min_rows"])
        features["high_dimension"] = (columns > thresholds["high_dimension_min_features"])

        numeric_count = 0
        categorical_count = 0

        for column, info in context.columns.items():
            semantic_type = info.get("semantic_type")

            if semantic_type == "numerical":
                numeric_count += 1

            elif semantic_type == "categorical":
                categorical_count += 1



        features["numeric_features"] = (numeric_count > 0)
        features["categorical_features"] = (categorical_count > 0)
        features["mixed_features"] = (numeric_count > 0 and categorical_count > 0)

        return features