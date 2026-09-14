import pandas as pd

from ml_engine.preprocessing.pipeline import PreprocessingPipeline
from ml_engine.model_execution.executor import ModelExecutionService



def test_kmeans_execution():

    df = pd.read_excel("data/customer_dataset.xlsx")
    pipeline = PreprocessingPipeline(df,"clustering",None)
    processed = pipeline.process()
    service = ModelExecutionService()
    result = service.execute("KMeans",processed["dataframe"],None,"clustering")
    assert "metrics" in result
    assert "number_of_clusters" in result["metrics"]