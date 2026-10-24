from ml_engine.dataset_loader import load_dataset


def test_excel_loading():

    file_path = "data/test.xlsx"

    dataframe = load_dataset(file_path)

    assert dataframe is not None