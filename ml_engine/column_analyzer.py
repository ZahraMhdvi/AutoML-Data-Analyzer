class ColumnAnalyzer:

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def get_column_type(self, column):
        dtype = self.dataframe[column].dtype
        return str(dtype)

    def is_numerical(self, column):
        return self.dataframe[column].dtype in [
            "int64",
            "float64"]

    def is_categorical(self, column):

        unique_count = self.dataframe[column].nunique()
        return unique_count < 20

    def is_identifier(self, column):

        unique_count = self.dataframe[column].nunique()

        row_count = len(self.dataframe)

        high_uniqueness = (unique_count / row_count) > 0.9

        return ( high_uniqueness and self.has_id_name(column)
                 )

    def has_id_name(self, column):

        column_name = column.lower()

        keywords = [
            "id",
            "code",
            "uuid"
        ]

        return any(
            keyword in column_name
            for keyword in keywords
        )

    def analyze(self):

        result = {}

        for column in self.dataframe.columns:

            if self.is_identifier(column):

                semantic_type = "identifier"

            elif self.is_numerical(column):

                semantic_type = "numerical"

            elif self.is_categorical(column):

                semantic_type = "categorical"

            else:

                semantic_type = "unknown"

            result[column] = {
                "technical_type": str(
                    self.dataframe[column].dtype
                ),
                "semantic_type": semantic_type
            }

        return result
