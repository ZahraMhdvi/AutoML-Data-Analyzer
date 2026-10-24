"""Model factory.  Every model is created with explicit, recorded hyper-parameters."""

from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from ml_engine.model_execution.clustering_optimizer import ClusteringOptimizer
from ml_engine.model_execution.dbscan_optimizer import DBSCANOptimizer

try:

    from xgboost import XGBClassifier
except Exception:

    XGBClassifier = None


SEED = 42


def classifier_params(algorithm, n_train_rows, seed=SEED):
    if algorithm == "Logistic Regression":
        return {"max_iter": 2000}
    if algorithm == "Decision Tree":
        return {"random_state": seed}
    if algorithm == "Random Forest":
        return {"n_estimators": 200, "random_state": seed, "n_jobs": -1}
    if algorithm == "XGBoost":
        return {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 6, "random_state": seed,
                "n_jobs": 4, "verbosity": 0}
    if algorithm == "SVM":
        return {"kernel": "rbf", "C": 1.0, "gamma": "scale"}
    if algorithm == "KNN":
        return {"n_neighbors": max(1, min(5, n_train_rows - 1))}
    raise ValueError(f"Unknown classifier: {algorithm}")


def build_classifier(algorithm, n_train_rows, seed=SEED):
    params = classifier_params(algorithm, n_train_rows, seed)
    factory = {
        "Logistic Regression": LogisticRegression,
        "Decision Tree": DecisionTreeClassifier,
        "Random Forest": RandomForestClassifier,
        "XGBoost": XGBClassifier,
        "SVM": SVC,
        "KNN": KNeighborsClassifier,
    }[algorithm]
    if factory is None:
        raise ValueError("XGBoost is not installed")
    return factory(**params), params


def build_clusterer(algorithm, X, cluster_count=None, seed=SEED):



    if algorithm == "KMeans":
        selection = None
        if not cluster_count:
            selection = ClusteringOptimizer().find_best_k(X)
            cluster_count = selection["n_clusters"]
        params = {"n_clusters": int(cluster_count), "n_init": 10, "random_state": seed}
        return KMeans(**params), params, selection

    if algorithm == "Agglomerative Clustering":
        selection = None
        if not cluster_count:
            selection = ClusteringOptimizer().find_best_k(X, model="agglomerative")
            cluster_count = selection["n_clusters"]
        params = {"n_clusters": int(cluster_count), "linkage": "ward"}
        return AgglomerativeClustering(**params), params, selection

    if algorithm == "DBSCAN":
        selection = DBSCANOptimizer().find_best_config(X)
        if selection:
            params = {"eps": selection["eps"], "min_samples": selection["min_samples"]}
        else:
            params = {"eps": 0.5, "min_samples": 5}
            selection = {"fallback": True}
        return DBSCAN(**params), params, selection

    raise ValueError(f"Unknown clustering algorithm: {algorithm}")


def clone_clusterer(algorithm, params):
    factory = {"KMeans": KMeans, "Agglomerative Clustering": AgglomerativeClustering, "DBSCAN": DBSCAN}[algorithm]
    return factory(**params)


class ModelTrainer:


    def train(self, algorithm_name, X, y=None, cluster_count=None):
        if y is not None:
            model, _ = build_classifier(algorithm_name, len(X))
            return model.fit(X, y)
        model, _, _ = build_clusterer(algorithm_name, X, cluster_count)
        return model.fit(X)
