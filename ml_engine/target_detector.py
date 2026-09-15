class TargetDetector:

    def __init__(
        self,
        dataframe,
        column_analysis
    ):
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
            "fraud",
            "response",
            "default",
            "diagnosis"
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

        return 2 <= unique_count <= 20


    def detect(self):

        candidates = []


        for column, info in self.column_analysis.items():

            if info["semantic_type"] == "identifier":
                continue


            score = 0
            reasons = []


            if self.has_target_keyword(column):

                score += 80

                reasons.append(
                    "Target keyword detected"
                )


            if self.has_reasonable_classes(column):

                score += 20

                reasons.append(
                    "Reasonable number of classes"
                )


            # فقط Targetهای با اطمینان بالا
            if score >= 80:

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