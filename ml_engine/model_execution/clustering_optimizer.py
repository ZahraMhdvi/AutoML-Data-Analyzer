
import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score


MAX_SELECTION_ROWS = 4000


class ClusteringOptimizer:

    def find_best_k(self, X, min_k=2, max_k=10, model="kmeans", seed=42):
        X = np.asarray(X, dtype=float)
        n = len(X)

        if n < 3:
            return {"n_clusters": min(2, max(n, 1)), "silhouette_score": None, "candidates": []}

        max_k = min(max_k, n - 1)

        rng = np.random.default_rng(seed)
        sample = X if n <= MAX_SELECTION_ROWS else X[rng.choice(n, MAX_SELECTION_ROWS, replace=False)]

        best_k, best_score, candidates = min_k, -1.0, []

        for k in range(min_k, max_k + 1):
            if model == "agglomerative":
                labels = AgglomerativeClustering(n_clusters=k).fit_predict(sample)
            else:
                labels = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(sample)

            n_labels = len(set(labels))
            if n_labels < 2 or n_labels > len(sample) - 1:
                continue

            score = float(silhouette_score(sample, labels))
            candidates.append({"k": k, "silhouette": round(score, 4)})

            if score > best_score:
                best_score, best_k = score, k

        return {
            "criterion": "silhouette",
            "n_clusters": best_k,
            "silhouette_score": best_score if candidates else None,
            "candidates": candidates,
        }
