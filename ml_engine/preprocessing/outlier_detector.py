import pandas as pd


class OutlierDetector:


    def __init__(self, dataframe):

        self.dataframe = dataframe



    def get_numeric_columns(self):

        return [
            column
            for column in self.dataframe.columns
            if pd.api.types.is_numeric_dtype(self.dataframe[column])]





    def detect_outliers(self):

        result = {}
        numeric_columns = self.get_numeric_columns()
        for column in numeric_columns:
            q1 = self.dataframe[column].quantile(0.25)
            q3 = self.dataframe[column].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outliers = self.dataframe[(self.dataframe[column] < lower_bound)|(self.dataframe[column] > upper_bound)]
            result[column] = len(outliers)

        return result



    def remove_outliers(self):

        df = self.dataframe.copy()
        for column in self.get_numeric_columns():
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            df = df[(df[column] >= lower_bound)&(df[column] <= upper_bound)]

        return df