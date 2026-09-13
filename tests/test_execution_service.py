import pandas as pd

from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.model_execution.executor import ModelExecutionService

def test_classification_execution():


    df = pd.read_excel("data/customer_dataset.xlsx")
    pipeline = PreprocessingPipeline(df,"classification","Churn")
    result = pipeline.process()
    service = ModelExecutionService()
    output = service.execute(
        "Random Forest",
        result["dataframe"],
        result["target"],
        "classification"
    )

    assert "metrics" in output