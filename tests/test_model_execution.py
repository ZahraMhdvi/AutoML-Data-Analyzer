import pandas as pd

from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.model_execution.trainer import ModelTrainer
from ml_engine.model_execution.evaluator import ModelEvaluator

def test_random_forest_execution():


    df = pd.read_excel("data/customer_dataset.xlsx")
    pipeline = PreprocessingPipeline(df,"classification","Churn")
    processed = pipeline.process()
    X = processed["dataframe"]
    y = processed["target"]
    trainer = ModelTrainer()
    model = trainer.train("Random Forest",X,y)
    evaluator = ModelEvaluator()
    result = evaluator.evaluate(model,X,y,"classification")
    assert "accuracy" in result