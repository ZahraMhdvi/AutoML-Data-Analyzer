from ml_engine.preprocessing.missing_handler import MissingHandler
from ml_engine.dataset_loader import DatasetLoader


loader = DatasetLoader()
df = loader.load_excel("data/test_missing.xlsx")
handler = MissingHandler(df)
print(handler.get_missing_report())
clean_df = handler.fill_missing()
print(clean_df)