from ml_engine.dataset_loader import DatasetLoader
from ml_engine.column_analyzer import ColumnAnalyzer
from ml_engine.target_detector import TargetDetector


loader = DatasetLoader()
df = loader.load_excel("data/customers.xlsx")
analyzer = ColumnAnalyzer(df)
analysis = analyzer.analyze()
detector = TargetDetector(df,analysis)
result = detector.detect()
print(result)