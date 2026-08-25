import pandas as pd


class MissingHandler:

    def __init__(self, dataframe):

        self.dataframe = dataframe


    def get_missing_report(self):

        missing = self.dataframe.isnull().sum()

        return missing.to_dict()



    def fill_missing(self):

        df = self.dataframe.copy()


        for column in df.columns:


            if df[column].isnull().sum() == 0:
                continue


            if pd.api.types.is_numeric_dtype(df[column]):

                df[column] = df[column].fillna(df[column].median())

            else:

                df[column] = df[column].fillna(df[column].mode()[0])

        return df