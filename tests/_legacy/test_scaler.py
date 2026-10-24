from ml_engine.dataset_loader import DatasetLoader
from ml_engine.preprocessing.scaler import FeatureScaler


loader = DatasetLoader()
df = loader.load_excel("data/test_scaler.xlsx")
scaler = FeatureScaler(df)
scaled_df = scaler.scale()
print(scaled_df)