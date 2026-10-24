
import argparse, json, os, subprocess, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SETS = ["iris", "wine", "breast_cancer", "titanic", "penguins", "telco_churn", "pima_diabetes", "banknote",
        "ionosphere", "sonar", "glass", "seeds", "haberman", "guidml_customers"]
ALGOS = ["Logistic Regression", "Random Forest", "KNN"]

ORIGINAL_SNIPPET = r'''
import json, sys, warnings, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, sys.argv[1])
from ml_engine.model_execution.runner import run_model_on_dataframe
df = pd.read_csv(sys.argv[2]); r = run_model_on_dataframe(df, sys.argv[3], "classification", sys.argv[4])
print(json.dumps({"accuracy": r["metrics"]["accuracy"], "weighted_f1": r["metrics"]["f1"],
                  "rows_used": r["data_summary"]["rows_used"], "test_size": r["metrics"]["test_size"]}))
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clean"))
    ap.add_argument("--out", default=os.path.join(HERE, "results", "e5_leakage_comparison.csv"))
    a = ap.parse_args()
    sys.path.insert(0, ROOT)
    from ml_engine.model_execution.runner import run_classification
    manifest = {m["name"]: m for m in json.load(open(os.path.join(a.data, "manifest.json")))}
    rows = []
    for name in SETS:
        path = os.path.join(a.data, f"{name}.csv"); target = manifest[name]["target"]
        df = pd.read_csv(path)
        for algo in ALGOS:
            out = subprocess.run([sys.executable, "-I", "-c", ORIGINAL_SNIPPET, a.original, path, algo, target],
                                 capture_output=True, text=True, cwd=a.original)
            try:
                orig = json.loads(out.stdout.strip().splitlines()[-1])
            except Exception:
                orig = {"error": (out.stderr.strip().splitlines() or ["?"])[-1][:160]}
            new = run_classification(df, algo, {"type": "observed", "column": target}, compute_cv=False, compute_permutation=False)
            rows.append({"dataset": name, "algorithm": algo, "rows": len(df),
                         "orig_rows_used": orig.get("rows_used"), "orig_accuracy": orig.get("accuracy"),
                         "orig_weighted_f1": orig.get("weighted_f1"), "orig_error": orig.get("error"),
                         "new_rows_used": new["data_summary"]["rows_used"], "new_accuracy": new["metrics"]["accuracy"],
                         "new_weighted_f1": new["metrics"]["weighted_f1"]})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(a.out, index=False)

if __name__ == "__main__":
    main()
