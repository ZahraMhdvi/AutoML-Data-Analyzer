import pandas as pd


def load_dataset(file_path):


    try:
        dataframe = pd.read_excel(file_path)
        return dataframe

    except Exception as error:
        raise Exception(f"Failed to load dataset: {error}")