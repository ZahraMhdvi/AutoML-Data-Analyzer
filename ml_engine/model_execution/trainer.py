from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import AgglomerativeClustering
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

from ml_engine.model_execution.clustering_optimizer import ClusteringOptimizer
from ml_engine.model_execution.dbscan_optimizer import DBSCANOptimizer


class ModelTrainer:

    def __init__(self):

        self.cluster_optimizer = ClusteringOptimizer()

        self.dbscan_optimizer = DBSCANOptimizer()

    def train(
            self,
            algorithm_name,
            X,
            y=None,
            cluster_count=None
    ):

        if (
                algorithm_name == "KMeans"
                and cluster_count
        ):

            model = KMeans(
                n_clusters=cluster_count,
                random_state=42
            )


        elif (
                algorithm_name == "Agglomerative Clustering"
                and cluster_count
        ):

            model = AgglomerativeClustering(
                n_clusters=cluster_count
            )


        elif (
                algorithm_name == "KMeans"
                and y is None
        ):

            best_config = self.cluster_optimizer.find_best_k(X)

            model = KMeans(
                n_clusters=best_config["n_clusters"],
                random_state=42
            )

        elif algorithm_name == "DBSCAN":

            best_config = (
                self.dbscan_optimizer
                .find_best_config(X)
            )

            if best_config:

                model = DBSCAN(
                    eps=best_config["eps"],
                    min_samples=best_config["min_samples"]
                )


            else:

                model = DBSCAN(
                    eps=0.5,
                    min_samples=5
                )

        else:

            model = self._create_model(
                algorithm_name
            )


        if y is not None:
            model.fit(X,y)

        else:

            model.fit(X)

        return model

    def _create_model(self, algorithm_name, X=None):

        if algorithm_name == "KMeans":
            best_config = self.cluster_optimizer.find_best_k(X)

            return KMeans(
                n_clusters=best_config["n_clusters"],
                random_state=42
            )

        models = {


            "Logistic Regression":
                LogisticRegression(max_iter=2000),

            "Decision Tree":
                DecisionTreeClassifier(random_state=42),

            "Random Forest":
                RandomForestClassifier(random_state=42),

            "XGBoost":
                XGBClassifier(random_state=42),

            "SVM":
                SVC(),

            "KNN":
                KNeighborsClassifier(),

            "DBSCAN":
                DBSCAN(
                    eps=0.8,
                    min_samples=5
                ),

            "Agglomerative Clustering":
                AgglomerativeClustering()

        }

        return models[algorithm_name]