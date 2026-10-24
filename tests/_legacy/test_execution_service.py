import pytest
import pandas as pd
from ml_engine.model_execution.executor import ModelExecutionService
from ml_engine.preprocessing.pipeline import PreprocessingPipeline


@pytest.mark.parametrize(
    "algorithm",
    [
        "Logistic Regression",
        "Decision Tree",
        "Random Forest",
        "XGBoost",
        "SVM",
        "KNN"
    ]
)
def test_classification_models(algorithm):


    df = pd.read_excel("data/customer_dataset.xlsx")


    pipeline = PreprocessingPipeline(
        df,
        "classification",
        "Churn"
    )


    processed = pipeline.process()


    service = ModelExecutionService()


    result = service.execute(
        algorithm,
        processed["dataframe"],
        processed["target"],
        "classification"
    )


    assert "metrics" in result