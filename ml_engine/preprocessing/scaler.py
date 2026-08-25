from sklearn.preprocessing import StandardScaler


class FeatureScaler:


    def __init__(self,dataframe,numeric_columns):

        self.dataframe = dataframe
        self.numeric_columns = numeric_columns



    def scale(self):
        df = self.dataframe.copy()
        scaler = StandardScaler()
        df[self.numeric_columns] = scaler.fit_transform(df[self.numeric_columns])

        return df


