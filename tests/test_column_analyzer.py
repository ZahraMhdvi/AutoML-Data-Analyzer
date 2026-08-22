from ml_engine.dataset_loader import DatasetLoader
from ml_engine.column_analyzer import ColumnAnalyzer


loader = DatasetLoader()

df = loader.load_excel("data/customers.xlsx")
analyzer = ColumnAnalyzer(df)
result = analyzer.analyze()
print(result)