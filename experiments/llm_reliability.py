
import argparse, json, os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ml_engine.ai.llm_target_service import LLMTargetServiceError, build_prompt_profile, get_llm_service  # noqa: E402
from ml_engine.ai.target_generator import new_definition  # noqa: E402
from ml_engine.column_analyzer import ColumnAnalyzer  # noqa: E402
from ml_engine.model_execution.runner import run_classification  # noqa: E402
from ml_engine.model_execution.split_manager import batch_split  # noqa: E402

SETS = [("guidml_clustering", None), ("mall_customers", None), ("wine", "class"), ("seeds", "variety"),
        ("pima_diabetes", "outcome"), ("guidml_customers", "Churn")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(ROOT, "experiments", "results", "e6_llm_reliability.csv"))
    a = ap.parse_args()
    service = get_llm_service()
    if service is None:
        sys.exit("OPENROUTER_API_KEY is not configured")
    rows = []
    for name, label in SETS:
        df = pd.read_csv(os.path.join(a.data, f"{name}.csv"))
        if label:
            df = df.drop(columns=[label])
        train, _, _ = batch_split(len(df), None, None)
        fit = df.iloc[train]
        analysis = ColumnAnalyzer(fit).analyze()
        profile = build_prompt_profile(fit, analysis)
        numeric = [c for c, i in analysis.items() if i["semantic_type"] == "numerical"]
        for rep in range(a.repeats):
            row = {"dataset": name, "repeat": rep}
            try:
                suggestion, record = service.suggest(profile, numeric)
                mentioned = sum(f.lower() in (suggestion["reason_en"] or "").lower() for f in suggestion["features"])
                row.update(status="SUCCESS", model=record["successful_model"], latency_ms=record["latency_ms"],
                           attempts=len(record["attempts"]), features="|".join(suggestion["features"]),
                           rejected="|".join(suggestion["rejected_features"]),
                           explanation_mentions_features=mentioned / len(suggestion["features"]))
                ab = run_classification(df, "Random Forest", {"type": "pseudo", "definition": new_definition(
                    suggestion["features"], "llm", suggestion["directions"])}, compute_cv=False,
                    compute_permutation=False)["ablation"]
                row.update(A_macro_f1=ab["condition_a_with_generator_features"]["macro_f1"],
                           B_macro_f1=(ab["condition_b_without_generator_features"] or {}).get("macro_f1"),
                           R=ab["reconstructability_R"], H=ab["normalized_entropy_H"])
            except LLMTargetServiceError as exc:
                row.update(status="FAILED", latency_ms=exc.record.get("latency_ms"),
                           attempts=len(exc.record.get("attempts", [])),
                           error_codes="|".join(x["error_code"] for x in exc.record.get("attempts", [])))
            rows.append(row)
            print(row, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(a.out, index=False)
    print(out.groupby("dataset")["status"].value_counts())


if __name__ == "__main__":
    main()
