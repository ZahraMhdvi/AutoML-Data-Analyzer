class DatasetProfiler:

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def get_shape(self):
        return {
            "rows": self.dataframe.shape[0],
            "columns": self.dataframe.shape[1]
        }


    def get_missing_values(self):

        missing = self.dataframe.isnull().sum()

        return missing.to_dict()



    def get_duplicates(self):

        duplicates = self.dataframe.duplicated().sum()

        return int(duplicates)



    def generate_report(self):

        return {
            "shape": self.get_shape(),
            "missing_values": self.get_missing_values(),
            "duplicates": self.get_duplicates()
        }