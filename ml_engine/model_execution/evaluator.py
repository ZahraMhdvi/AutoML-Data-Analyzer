from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    silhouette_score,
    confusion_matrix
)



class ModelEvaluator:


    def evaluate(self,model,X,y=None,problem_type=None):


        if problem_type == "classification":
            return self._classification_metrics(model,X,y)

        elif problem_type == "clustering":
            return self._clustering_metrics(model,X)

        else:
            raise ValueError("Unsupported problem type")

    def _classification_metrics(self,model,X,y):

        predictions = model.predict(X)
        matrix = confusion_matrix(
            y,
            predictions
        )

        classes = [
            str(label)
            for label in sorted(set(y))
        ]

        return {

            "accuracy":
                accuracy_score(
                    y,
                    predictions
                ),

            "precision":
                precision_score(
                    y,
                    predictions,
                    average="weighted"
                ),

            "recall":
                recall_score(
                    y,
                    predictions,
                    average="weighted"
                ),

            "f1":
                f1_score(
                    y,
                    predictions,
                    average="weighted"
                ),

            "confusion_matrix":
                [
                    [
                        int(value)
                        for value in row
                    ]
                    for row in matrix
                ],

            "classes":
                [
                    str(label)
                    for label in sorted(set(y))
                ]

        }



    def _clustering_metrics(self,model,X):

        labels = model.labels_
        unique_labels = set(labels)
        clusters = len(unique_labels - {-1})

        noise = sum(1 for label in labels if label == -1)
        result = {

            "number_of_clusters": clusters,
            "noise_points": noise
        }

        if clusters > 1:
            result["silhouette_score"] = (silhouette_score(X,labels))

        else:

            result["silhouette_score"] = None

        return result