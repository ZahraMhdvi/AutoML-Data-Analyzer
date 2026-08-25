import pandas as pd

from sklearn.preprocessing import LabelEncoder

class CategoricalEncoder:


    def __init__(self, dataframe):

        self.dataframe = dataframe

    def get_categorical_columns(self):

        return list(
            self.dataframe.select_dtypes(
                include=["object", "string"]
            ).columns
        )




    def encode(self):

        print(self.dataframe.dtypes)

        df = self.dataframe.copy()

        categorical_columns = self.get_categorical_columns()

        print(categorical_columns)

        for column in categorical_columns:

            unique_count = df[column].nunique()

            if unique_count == 2:

                encoder = LabelEncoder()

                df[column] = encoder.fit_transform(df[column])


            else:

                df = pd.get_dummies(df,columns=[column])

        return df