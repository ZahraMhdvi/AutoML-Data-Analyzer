from ml_engine.dataset_loader import DatasetLoader
from ml_engine.column_analyzer import ColumnAnalyzer
from ml_engine.target_detector import TargetDetector
from ml_engine.eligibility import EligibilityChecker


loader = DatasetLoader()

df = loader.load_excel("data/customers.xlsx")
column_analyzer = ColumnAnalyzer(df)
column_analysis = column_analyzer.analyze()
target_detector = TargetDetector(df,column_analysis)
targets = target_detector.detect()
checker = EligibilityChecker(df,column_analysis,targets)
result = checker.evaluate()
print(result)