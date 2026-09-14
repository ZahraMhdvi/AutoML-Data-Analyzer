from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import AgglomerativeClustering

from ml_engine.model_execution.clustering_optimizer import ClusteringOptimizer


class ModelTrainer:

    def __init__(self):

        self.cluster_optimizer = ClusteringOptimizer()

    def train(self,algorithm_name,X,y=None):

        if algorithm_name == "KMeans" and y is None:
            best_config = self.cluster_optimizer.find_best_k(X)
            model = KMeans(n_clusters=best_config["n_clusters"],random_state=42)

        else:

            model = self._create_model(algorithm_name)


        if y is not None:
            model.fit(X,y)

        else:

            model.fit(X)

        return model



    def _create_model(self,algorithm_name):

        models = {
            "Logistic Regression":
                LogisticRegression(),


            "Decision Tree":
                DecisionTreeClassifier(),


            "Random Forest":
                RandomForestClassifier(),


            "KMeans":
                KMeans(
                    n_clusters=3,
                    random_state=42
                ),


            "DBSCAN":
                DBSCAN(),


            "Agglomerative Clustering":
                AgglomerativeClustering()

        }


        if algorithm_name not in models:

            raise ValueError(
                f"Unsupported algorithm {algorithm_name}"
            )


        return models[algorithm_name]