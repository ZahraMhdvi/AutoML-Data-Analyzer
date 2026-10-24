

import argparse
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs, make_moons

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

from ml_engine.ai.target_generator import build_statistical_definition, fit_definition
from ml_engine.model_execution.runner import run_classification, run_clustering
from ml_engine.model_execution.split_manager import batch_split
from ml_engine.model_selection.algorithm_registry import CLASSIFICATION_ALGORITHMS, eligibility
from ml_engine.model_selection.application.model_selection_application import ModelSelectionApplication
CLASSIFIERS = list(CLASSIFICATION_ALGORITHMS)
CLASSIFICATION_SETS = ["iris", "wine", "breast_cancer", "digits", "titanic", "penguins", "telco_churn",
                       "pima_diabetes", "banknote", "ionosphere", "sonar", "glass", "seeds", "haberman", "ecoli",
                       "guidml_customers", "adult"]
PROFILES = {
    "accuracy": {"main_goal": "accuracy", "data_growth": "static_data"},
    "speed": {"main_goal": "speed", "data_growth": "static_data"},
    "interpretability": {"main_goal": "interpretability", "data_growth": "static_data"},
}


def load(data_dir, name):
    manifest = {m["name"]: m for m in json.load(open(os.path.join(data_dir, "manifest.json")))}
    return pd.read_csv(os.path.join(data_dir, f"{name}.csv")), manifest[name]


def e1_classification(data_dir):
    rows = []
    for name in CLASSIFICATION_SETS:
        df, meta = load(data_dir, name)
        for algorithm in CLASSIFIERS:
            reason = eligibility(algorithm, "classification", len(df))
            if reason:
                rows.append({"dataset": name, "algorithm": algorithm, "eligible": False, "excluded_reason": reason})
                continue
            start = time.perf_counter()
            r = run_classification(df, algorithm, {"type": "observed", "column": meta["target"]},
                                   compute_permutation=False)
            m, cv = r["metrics"], r["cross_validation"] or {}
            rows.append({
                "dataset": name, "algorithm": algorithm, "eligible": True,
                "rows": len(df), "train_rows": r["data_summary"]["train_rows"], "test_rows": r["data_summary"]["test_rows"],
                "accuracy": m["accuracy"], "balanced_accuracy": m["balanced_accuracy"],
                "macro_precision": m["macro_precision"], "macro_recall": m["macro_recall"],
                "macro_f1": m["macro_f1"], "weighted_f1": m["weighted_f1"],
                "cv_macro_f1_mean": (cv.get("macro_f1") or {}).get("mean"),
                "cv_macro_f1_std": (cv.get("macro_f1") or {}).get("std"),
                "train_ms": m["latency"]["train_ms"], "inference_ms": m["latency"]["inference_ms"],
                "wall_s": round(time.perf_counter() - start, 2),
            })
            print(f"E1 {name:18s} {algorithm:20s} acc={m['accuracy']:.3f} mF1={m['macro_f1']:.3f}", flush=True)
    return pd.DataFrame(rows)


def ndcg(ranking, gains):
    dcg = sum(gains[a] / np.log2(i + 2) for i, a in enumerate(ranking))
    ideal = sorted(gains.values(), reverse=True)
    idcg = sum(g / np.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def rank_metrics(ranking, perf):
    top = max(perf.values())
    winners = {a for a, v in perf.items() if v >= top - 1e-9}   # ties count as hits
    best = max(perf, key=perf.get)
    position = min(ranking.index(a) for a in winners) + 1
    lo, hi = min(perf.values()), max(perf.values())
    gains = {a: (perf[a] - lo) / (hi - lo) if hi > lo else 1.0 for a in perf}
    return {"top1": float(position == 1), "top3": float(position <= 3), "rr": 1.0 / position,
            "ndcg": ndcg(ranking, gains), "regret": perf[best] - perf[ranking[0]]}


def e2_selector(data_dir, e1, seed=0):
    app = ModelSelectionApplication()
    records, per_dataset = [], []
    rng = np.random.default_rng(seed)
    perf_table = e1[e1["eligible"]].pivot(index="dataset", columns="algorithm", values="macro_f1")

    for name in CLASSIFICATION_SETS:
        df, meta = load(data_dir, name)
        perf = perf_table.loc[name].dropna().to_dict()
        for profile, prefs in PROFILES.items():
            response = app.run_dataframe(df, "classification", meta["target"], dict(prefs), CLASSIFICATION_ALGORITHMS)
            ranking = [r.algorithm for r in response.recommendations if r.algorithm in perf]
            scores = {r.algorithm: r.score for r in response.recommendations}
            cs = rank_metrics(ranking, perf)
            per_dataset.append({"dataset": name, "profile": profile, "ranking": ranking, "scores": scores,
                                "empirical_best": max(perf, key=perf.get), **cs})

            rule = ["Random Forest"] + [a for a in CLASSIFIERS if a != "Random Forest" and a in perf]
            rb = rank_metrics(rule, perf)

            rand = [rank_metrics(list(rng.permutation(list(perf))), perf) for _ in range(2000)]
            rnd = {k: float(np.mean([r[k] for r in rand])) for k in rand[0]}

            for method, values in (("compatibility_score", cs), ("simple_rule_always_RF", rb), ("random", rnd)):
                records.append({"dataset": name, "profile": profile, "method": method, **values})
        print(f"E2 {name} done", flush=True)

    summary = (pd.DataFrame(records).groupby(["profile", "method"])[["top1", "top3", "rr", "ndcg", "regret"]]
               .mean().reset_index().rename(columns={"rr": "mrr"}))
    return summary, pd.DataFrame(per_dataset)


def clustering_sets(data_dir):
    sets = []
    for name, label in (("iris", "class"), ("wine", "class"), ("seeds", "variety"), ("penguins", "species")):
        df, _ = load(data_dir, name)
        df = df.dropna().reset_index(drop=True)
        sets.append((name, df.drop(columns=[label]).select_dtypes("number"), df[label].to_numpy()))
    X, y = make_blobs(n_samples=600, centers=4, cluster_std=1.0, random_state=7)
    sets.append(("synthetic_blobs", pd.DataFrame(X, columns=["x1", "x2"]), y))
    X, y = make_moons(n_samples=500, noise=0.06, random_state=7)
    sets.append(("synthetic_moons", pd.DataFrame(X, columns=["x1", "x2"]), y))
    for name in ("mall_customers", "guidml_clustering"):
        df, _ = load(data_dir, name)
        sets.append((name, df, None))
    return sets


def e3_clustering(data_dir):
    rows = []
    for name, frame, labels in clustering_sets(data_dir):
        for algorithm in ("KMeans", "Agglomerative Clustering", "DBSCAN"):
            r = run_clustering(frame, algorithm, reference_labels=labels)
            m = r["metrics"]
            ext = m["external"] or {}
            rows.append({
                "dataset": name, "algorithm": algorithm, "rows": len(frame),
                "true_k": int(len(set(labels))) if labels is not None else None,
                "k": m["cluster_count"], "silhouette": m["silhouette_score"],
                "davies_bouldin": m["davies_bouldin_index"], "calinski_harabasz": m["calinski_harabasz_index"],
                "noise_ratio": m["noise_ratio"], "stability_ari": (m["stability"] or {}).get("mean_ari"),
                "stability_std": (m["stability"] or {}).get("std_ari"),
                "ari": ext.get("adjusted_rand_index"), "nmi": ext.get("normalized_mutual_info"),
                "warnings": ",".join(m["warnings"]),
            })
            print(f"E3 {name:18s} {algorithm:25s} k={m['cluster_count']} sil={m['silhouette_score']}", flush=True)
    return pd.DataFrame(rows)


PSEUDO_SETS = [("guidml_clustering", None), ("mall_customers", None), ("wine", "class"), ("seeds", "variety"),
               ("breast_cancer", "class"), ("pima_diabetes", "outcome"), ("guidml_customers", "Churn"),
               ("telco_churn", "Churn")]


def e4_pseudo(data_dir):
    rows, drift_rows = [], []
    for name, label in PSEUDO_SETS:
        df, _ = load(data_dir, name)
        if label:
            df = df.drop(columns=[label])
        train, _, _ = batch_split(len(df), None, None)
        definition = build_statistical_definition(df.iloc[train])
        for algorithm in ("Decision Tree", "Random Forest", "Logistic Regression"):
            r = run_classification(df, algorithm, {"type": "pseudo", "definition": definition},
                                   compute_cv=False, compute_permutation=False)
            ab = r["ablation"]
            b = ab["condition_b_without_generator_features"] or {}
            rows.append({
                "dataset": name, "algorithm": algorithm, "generator_features": "|".join(ab["generator_features"]),
                "independent_features": ab["independent_feature_count"],
                "A_accuracy": ab["condition_a_with_generator_features"]["accuracy"],
                "A_macro_f1": ab["condition_a_with_generator_features"]["macro_f1"],
                "B_accuracy": b.get("accuracy"), "B_macro_f1": b.get("macro_f1"),
                "delta_macro_f1": ab["delta_macro_f1"], "reconstructability_R": ab["reconstructability_R"],
                "entropy_H": ab["normalized_entropy_H"],
            })
            print(f"E4 {name:18s} {algorithm:20s} A={rows[-1]['A_macro_f1']:.3f} B={rows[-1]['B_macro_f1']}", flush=True)

        n = len(df)
        batches = np.r_[np.ones(int(n * 0.6), int), np.full(int(n * 0.2), 2), np.full(n - int(n * 0.6) - int(n * 0.2), 3)]
        for version in (2, 3):
            mask = batches <= version
            r = run_classification(df.loc[mask].reset_index(drop=True), "Decision Tree",
                                   {"type": "pseudo", "definition": definition}, batch_ids=batches[mask],
                                   compute_cv=False, compute_permutation=False)
            d = r["ablation"].get("label_drift_if_regenerated") or {}
            drift_rows.append({"dataset": name, "version": version, "rows": int(mask.sum()),
                               "changed_ratio": d.get("changed_ratio"),
                               "frozen_cutoffs": d.get("frozen_cutoffs"), "refit_cutoffs": d.get("refit_cutoffs")})
    return pd.DataFrame(rows), pd.DataFrame(drift_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clean"))
    parser.add_argument("--out", default=os.path.join(ROOT, "experiments", "results"))
    parser.add_argument("--only", default="e1,e2,e3,e4")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    only = set(args.only.split(","))

    if "e1" in only:
        e1_classification(args.data).to_csv(os.path.join(args.out, "e1_classification.csv"), index=False)
    if "e2" in only:
        e1 = pd.read_csv(os.path.join(args.out, "e1_classification.csv"))
        summary, detail = e2_selector(args.data, e1)
        summary.to_csv(os.path.join(args.out, "e2_selector_summary.csv"), index=False)
        detail.to_json(os.path.join(args.out, "e2_selector_detail.json"), orient="records", indent=1)
    if "e3" in only:
        e3_clustering(args.data).to_csv(os.path.join(args.out, "e3_clustering.csv"), index=False)
    if "e4" in only:
        ablation, drift = e4_pseudo(args.data)
        ablation.to_csv(os.path.join(args.out, "e4_pseudo_ablation.csv"), index=False)
        drift.to_csv(os.path.join(args.out, "e4_label_drift.csv"), index=False)


if __name__ == "__main__":
    main()
