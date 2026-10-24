import numpy as np
import pandas as pd

from ml_engine.ai.target_generator import (
    PseudoTargetRule,
    build_statistical_definition,
    fit_definition,
    new_definition,
    normalized_entropy,
)
from ml_engine.model_execution.runner import run_classification


def _frame(n=300, seed=1):
    rng = np.random.default_rng(seed)
    a = rng.normal(0, 1, n)
    return pd.DataFrame({
        "spend": a * 10 + 50,
        "visits": a + rng.normal(0, 0.5, n),
        "tenure": rng.normal(0, 1, n),
        "noise": rng.normal(0, 1, n),
    })


def test_rule_is_fitted_on_training_rows_only():
    df = _frame()
    train = df.iloc[:200]
    rule = PseudoTargetRule(["spend", "visits"]).fit(train)

    mutated_test = df.copy()
    mutated_test.iloc[200:, 0] = 1e9
    rule2 = PseudoTargetRule(["spend", "visits"]).fit(mutated_test.iloc[:200])
    assert rule.fitted["cutoffs"] == rule2.fitted["cutoffs"]
    assert rule.fitted["train_distribution"] == {"Low": 67, "Medium": 66, "High": 67}


def test_rule_is_reconstructable_from_persisted_parameters():
    df = _frame()
    definition = new_definition(["spend", "visits"], source="llm", directions={"visits": -1})
    fitted, rule = fit_definition(definition, df.iloc[:200])
    restored = PseudoTargetRule.from_dict(fitted["fitted_rule"])
    assert (restored.transform(df) == rule.transform(df)).all()
    assert fitted["rule"]["name"] and fitted["fit_scope"] == "version_1_training_split"
    assert fitted["directions"] == {"spend": 1, "visits": -1}


def test_direction_reverses_ordering():
    df = _frame()
    up = PseudoTargetRule(["spend"]).fit(df).transform(df)
    down = PseudoTargetRule(["spend"], directions={"spend": -1}).fit(df).transform(df)
    top = df["spend"].idxmax()
    assert up[top] == "High" and down[top] == "Low"


def test_statistical_definition_records_provenance():
    definition = build_statistical_definition(_frame())
    assert definition["source"] == "statistical"
    assert definition["reason"]["code"] == "STATISTICAL_PCA"
    assert set(definition["features"]) <= {"spend", "visits", "tenure", "noise"}


def test_circularity_ablation_is_reported():
    df = _frame()
    definition = new_definition(["spend", "visits"], source="llm")
    result = run_classification(df, "Decision Tree", {"type": "pseudo", "definition": definition},
                                compute_cv=False, compute_permutation=False)
    ab = result["ablation"]
    assert ab["generator_features"] == ["spend", "visits"]
    a = ab["condition_a_with_generator_features"]["macro_f1"]
    b = ab["condition_b_without_generator_features"]["macro_f1"]
    assert a > b  # removing the generator features removes the shortcut
    assert ab["reconstructability_R"] > 0.8
    assert 0.95 <= ab["normalized_entropy_H"] <= 1.0
    assert result["fitted_target_definition"]["fitted_rule"]["fitted"]["n_fit_rows"] == 240


def test_normalized_entropy_bounds():
    assert normalized_entropy(["a", "b", "a", "b"]) == 1.0
    assert normalized_entropy(["a", "a", "a"]) == 0.0
