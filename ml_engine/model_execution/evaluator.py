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

        cluster_summary = []

        profile_X = X.drop(
            columns=[
                "Customer_ID",
                "Churn"
            ],
            errors="ignore"
        )

        for cluster in sorted(set(labels)):

            if cluster == -1:
                continue

            cluster_data = profile_X[
                labels == cluster
                ]

            cluster_summary.append({

                "cluster": int(cluster),

                "size": int(
                    len(cluster_data)
                ),

                "features": {

                    column:
                        float(
                            cluster_data[column].mean()
                        )

                    for column in cluster_data.columns

                }

            })

        cluster_profiles = (
            self._generate_dynamic_cluster_profiles(
                cluster_summary,
                X
            )
        )
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
                cluster_points,
            "cluster_summary":
                cluster_summary,
            "cluster_profiles":
                cluster_profiles,

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




    def _generate_cluster_profiles(
            self,
            cluster_summary
    ):

        profiles = []

        for cluster in cluster_summary:

            description = []

            features = cluster["features"]

            if features.get("Age", 0) < -0.5:

                description.append(
                    "Younger customers"
                )

            elif features.get("Age", 0) > 0.5:

                description.append(
                    "Older customers"
                )

            if features.get("Income", 0) > 0.5:

                description.append(
                    "Higher income"
                )

            elif features.get("Income", 0) < -0.5:

                description.append(
                    "Lower income"
                )

            if features.get("Tenure_Months", 0) < -0.5:

                description.append(
                    "New customers"
                )

            elif features.get("Tenure_Months", 0) > 0.5:

                description.append(
                    "Long-term customers"
                )

            if features.get("Num_Transactions", 0) > 0.5:

                description.append(
                    "High transaction activity"
                )

            elif features.get("Num_Transactions", 0) < -0.5:

                description.append(
                    "Low transaction activity"
                )

            if features.get("Support_Calls", 0) > 0.5:
                description.append(
                    "High support usage"
                )

            profiles.append({

                "cluster":
                    cluster["cluster"],

                "size":
                    cluster["size"],

                "description":
                    description

            })

        return profiles

    def _generate_dynamic_cluster_profiles(
            self,
            cluster_summary,
            X
    ):

        profiles = []

        global_mean = X.mean()

        for cluster in cluster_summary:

            features = cluster["features"]

            differences = {}

            for feature, value in features.items():
                differences[feature] = abs(
                    value - global_mean[feature]
                )

            important = sorted(
                differences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            profiles.append({

                "cluster":
                    cluster["cluster"],

                "size":
                    cluster["size"],

                    "important_features":[

                    {

                        "feature": feature,

                        "difference": float(
                            difference
                        ),

                        "direction":
                            (
                                "above_average"
                                if features[feature] > global_mean[feature]
                                else "below_average"
                            )

                    }

                    for feature, difference in important

                ]

            })

        return profiles