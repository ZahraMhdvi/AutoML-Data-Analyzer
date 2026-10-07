from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
import numpy as np


class DBSCANOptimizer:


    def find_best_config(self, X):

        best_config = None
        best_score = -1


        eps_values = np.arange(
            0.1,
            3.0,
            0.1
        )


        min_samples_values = [
            3,
            5,
            8,
            10,
            15
        ]


        for eps in eps_values:

            for min_samples in min_samples_values:


                model = DBSCAN(
                    eps=float(eps),
                    min_samples=min_samples
                )


                labels = model.fit_predict(X)


                unique_clusters = set(labels)

                clusters = (
                    len(
                        unique_clusters
                        -
                        {-1}
                    )
                )


                noise_points = list(labels).count(-1)


                noise_ratio = (
                    noise_points
                    /
                    len(labels)
                )


                if clusters < 2:
                    continue


                if noise_ratio > 0.4:
                    continue




                valid = labels != -1

                score = silhouette_score(
                    X[valid],
                    labels[valid]
                ) * (1 - noise_ratio)


                if score > best_score:


                    best_score = score


                    best_config = {

                        "eps": float(eps),

                        "min_samples":
                            min_samples,

                        "clusters":
                            clusters,

                        "noise":
                            noise_points,

                        "score":
                            float(score)

                    }



        return best_config