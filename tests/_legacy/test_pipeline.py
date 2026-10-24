from ml_engine.dataset_loader import DatasetLoader
from ml_engine.preprocessing.pipeline import PreprocessingPipeline


loader = DatasetLoader()
df = loader.load_excel("data/test_encoder.xlsx")
pipeline = PreprocessingPipeline(df)
clean_df = pipeline.process()
print(clean_df)