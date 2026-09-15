from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    silhouette_score,
    confusion_matrix
)
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


class ModelEvaluator:


    def evaluate(self,model,X,y=None,problem_type=None):


        if problem_type == "classification":
            return self._classification_metrics(model,X,y)

        elif problem_type == "clustering":
            return self._clustering_metrics(model,X)

        else:
            raise ValueError("Unsupported problem type")

    def _classification_metrics(self, model, X, y):

        predictions = model.predict(X)

        matrix = confusion_matrix(
            y,
            predictions
        )

        classes = [
            str(label)
            for label in sorted(set(y))
        ]

        feature_importance = None

        if hasattr(model, "feature_importances_"):
            feature_importance = [

                {
                    "feature": column,
                    "importance": float(value)
                }

                for column, value in zip(
                    X.columns,
                    model.feature_importances_
                )

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
                    average="weighted",
                    zero_division=0
                ),

            "recall":
                recall_score(
                    y,
                    predictions,
                    average="weighted",
                    zero_division=0
                ),

            "f1":
                f1_score(
                    y,
                    predictions,
                    average="weighted",
                    zero_division=0
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
                classes,

            "feature_importance":
                feature_importance

        }

    def _clustering_metrics(self, model, X):

        labels = model.labels_

        scaled_X = StandardScaler().fit_transform(X)

        pca = PCA(n_components=2)

        reduced = pca.fit_transform(
            scaled_X
        )

        cluster_points = [

            {
                "x": float(point[0]),
                "y": float(point[1]),
                "cluster": int(label)
            }

            for point, label in zip(
                reduced,
                labels
            )

        ]
        cluster_sizes = {
            str(label): int(count)
            for label, count in Counter(labels).items()
        }
        unique_labels = set(labels)

        clusters = len(
            unique_labels - {-1}
        )

        noise = sum(
            1
            for label in labels
            if label == -1
        )

        result = {

            "cluster_count":
                clusters,

            "noise_points":
                noise,
            "cluster_sizes":
                cluster_sizes,
            "cluster_points":
                cluster_points

        }

        if clusters > 1:

            result["silhouette_score"] = (
                silhouette_score(
                    X,
                    labels
                )
            )

        else:

            result["silhouette_score"] = None

        return result