from ml_engine.dataset_loader import DatasetLoader
from ml_engine.profiler import DatasetProfiler


loader = DatasetLoader()

df = loader.load_excel("data/customers.xlsx")

profiler = DatasetProfiler(df)
report = profiler.generate_report()

print(report)