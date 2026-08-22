class TargetDetector:

    def __init__(self, dataframe, column_analysis):
        self.dataframe = dataframe
        self.column_analysis = column_analysis

    def has_target_keyword(self, column):

        keywords = [
            "target",
            "label",
            "class",
            "status",
            "result",
            "outcome",
            "churn",
            "bought",
            "purchase",
            "fraud"
        ]

        column_name = column.lower()

        return any(
            word in column_name
            for word in keywords
        )

    def has_reasonable_classes(self, column):

        unique_count = (
            self.dataframe[column]
            .nunique()
        )

        return unique_count <= 20

    def detect(self):

        candidates = []
        for column, info in self.column_analysis.items():
            if info["semantic_type"] == "identifier":
                continue
            if info["semantic_type"] == "numerical":
                continue
            score = 0
            reasons = []

            if self.has_reasonable_classes(column):
                score += 50

                reasons.append(
                    "Low number of unique classes"
                )

            if self.has_target_keyword(column):
                score += 50

                reasons.append(
                    "Target keyword detected"
                )

            if score > 0:
                candidates.append(
                    {
                        "column": column,
                        "score": score,
                        "reason": reasons
                    }
                )

        return sorted(
            candidates,
            key=lambda x: x["score"],
            reverse=True
        )
