from ml_engine.dataset_loader import DatasetLoader

loader = DatasetLoader()

data = loader.load_excel("data/customers.xlsx")

print(data)