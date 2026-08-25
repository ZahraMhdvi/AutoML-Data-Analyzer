from sklearn.preprocessing import StandardScaler


class FeatureScaler:


    def __init__(self, dataframe):

        self.dataframe = dataframe



    def scale(self):

        df = self.dataframe.copy()
        numeric_columns = df.select_dtypes(include=["int64", "float64"]).columns
        scaler = StandardScaler()
        df[numeric_columns] = scaler.fit_transform(df[numeric_columns])


        return df


    