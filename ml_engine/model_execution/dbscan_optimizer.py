

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors


MAX_SELECTION_ROWS = 3000
MAX_NOISE_RATIO = 0.4


class DBSCANOptimizer:

    def find_best_config(self, X, seed=42):
        X = np.asarray(X, dtype=float)
        n = len(X)
        if n < 6:
            return None

        rng = np.random.default_rng(seed)
        sample = X if n <= MAX_SELECTION_ROWS else X[rng.choice(n, MAX_SELECTION_ROWS, replace=False)]

        eps_values = self._eps_grid(sample)
        min_samples_values = [m for m in (3, 5, 8, 10, 15) if m < len(sample)]

        best_config, best_score = None, -1.0

        for eps in eps_values:
            for min_samples in min_samples_values:
                labels = DBSCAN(eps=float(eps), min_samples=min_samples).fit_predict(sample)
                clusters = len(set(labels) - {-1})
                noise_ratio = float(np.mean(labels == -1))

                if clusters < 2 or noise_ratio > MAX_NOISE_RATIO:
                    continue

                valid = labels != -1
                if len(set(labels[valid])) < 2 or valid.sum() <= len(set(labels[valid])):
                    continue

                score = float(silhouette_score(sample[valid], labels[valid])) * (1 - noise_ratio)

                if score > best_score:
                    best_score = score
                    best_config = {
                        "eps": round(float(eps), 4),
                        "min_samples": int(min_samples),
                        "clusters": int(clusters),
                        "noise_ratio": round(noise_ratio, 4),
                        "score": round(score, 4),
                        "criterion": "silhouette_non_noise_x_(1-noise_ratio)",
                    }

        return best_config

    @staticmethod
    def _eps_grid(sample):


        k = min(5, len(sample) - 1)
        distances, _ = NearestNeighbors(n_neighbors=k + 1).fit(sample).kneighbors(sample)
        kth = distances[:, -1]
        adaptive = np.quantile(kth, np.linspace(0.5, 0.98, 12))
        fixed = np.arange(0.2, 3.01, 0.2)
        grid = np.unique(np.round(np.concatenate([adaptive, fixed]), 4))
        return grid[grid > 0]
