from ml_engine.analyzer_service import DatasetAnalyzer


analyzer = DatasetAnalyzer()
result = analyzer.analyze("data/customers.xlsx")
print(result)