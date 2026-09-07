class ContextFeatureExtractor:

    def extract(self,context):

        features = {}
        rows = context.clean_data_shape["rows"]
        columns = len(context.processed_columns)
        features["small_dataset"] = rows < 500
        features["large_dataset"] = rows > 5000
        features["high_dimension"] = columns > 50

        has_numeric = False
        has_categorical = False

        for column_info in context.raw_columns.values():

            semantic_type = column_info.get(
                "semantic_type"
            )
            if semantic_type == "numerical":
                has_numeric = True

            if semantic_type == "categorical":
                has_categorical = True

        features["numeric_features"] = has_numeric
        features["categorical_features"] = has_categorical
        features["mixed_features"] = (has_numeric and has_categorical)


        return features