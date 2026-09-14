from ml_engine.preprocessing.missing_handler import MissingHandler
from ml_engine.preprocessing.outlier_detector import OutlierDetector
from ml_engine.preprocessing.encoder import CategoricalEncoder
from ml_engine.preprocessing.scaler import FeatureScaler
from sklearn.preprocessing import LabelEncoder

class PreprocessingPipeline:


    def __init__(
            self,
            dataframe,
            problem_type,
            target=None
    ):

        self.dataframe = dataframe

        self.problem_type = problem_type

        self.target = target



    def process(self):


        df = self.dataframe.copy()


        target_column = None

        if self.problem_type == "classification":

            if self.target in df.columns:
                target_column = df[self.target]

                df = df.drop(
                    columns=[self.target]
                )

                encoder = LabelEncoder()

                target_column = encoder.fit_transform(
                    target_column
                )



        elif self.problem_type == "clustering":

            if self.target and self.target in df.columns:
                df = df.drop(
                    columns=[self.target]
                )

        numeric_columns = list(

            df.select_dtypes(
                include=[
                    "int64",
                    "float64"
                ]
            ).columns

        )
        missing_handler = MissingHandler(df)

        df = missing_handler.fill_missing()
        outlier_detector = OutlierDetector(df)
        df = outlier_detector.remove_outliers()

        encoder = CategoricalEncoder(df)

        df = encoder.encode()


        scaler = FeatureScaler(
            df,
            numeric_columns
        )

        df = scaler.scale()


        return {

            "dataframe": df,

            "target": target_column

        }