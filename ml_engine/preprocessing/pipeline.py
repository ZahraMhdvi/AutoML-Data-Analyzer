from ml_engine.preprocessing.missing_handler import MissingHandler
from ml_engine.preprocessing.outlier_detector import OutlierDetector
from ml_engine.preprocessing.encoder import CategoricalEncoder
from ml_engine.preprocessing.scaler import FeatureScaler


class PreprocessingPipeline:


    def __init__(self, dataframe):

        self.dataframe = dataframe

    def process(self):
        df = self.dataframe.copy()

        numeric_columns = list(df.select_dtypes( include=["int64", "float64"]).columns)
        missing_handler = MissingHandler(df)

        df = missing_handler.fill_missing()
        outlier_detector = OutlierDetector(df)
        df = outlier_detector.remove_outliers()
        encoder = CategoricalEncoder(df)
        df = encoder.encode()
        scaler = FeatureScaler(df,numeric_columns)
        df = scaler.scale()

        return df