from ml_engine.dataset_loader import DatasetLoader
from ml_engine.preprocessing.encoder import CategoricalEncoder


loader = DatasetLoader()
df = loader.load_excel("data/test_encoder.xlsx")
encoder = CategoricalEncoder(df)
encoded_df = encoder.encode()
print(encoded_df)