from ml_engine.dataset_loader import DatasetLoader
from ml_engine.preprocessing.outlier_detector import OutlierDetector


loader = DatasetLoader()
df = loader.load_excel("data/test_outlier.xlsx")
detector = OutlierDetector(df)
print(detector.detect_outliers())
clean_df = detector.remove_outliers()
print(clean_df)