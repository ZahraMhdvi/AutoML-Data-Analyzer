import pandas as pd


class DatasetLoader:

    def load_excel(self, file_path):

        dataframe = pd.read_excel(file_path)

        return dataframe