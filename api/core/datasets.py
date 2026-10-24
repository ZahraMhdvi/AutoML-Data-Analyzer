
import io
import os

import pandas as pd


ALLOWED_EXTENSIONS = (".xlsx", ".csv")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


from ml_engine.errors import AppError


class DatasetFileError(AppError):
    pass


def _extension(filename):
    return os.path.splitext(filename or "")[1].lower()


def check_extension(filename):

    ext = _extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise DatasetFileError("FILE_TYPE_NOT_SUPPORTED")

    return ext


def read_bytes(content, filename):

    ext = check_extension(filename)

    if not content:
        raise DatasetFileError("FILE_EMPTY")

    if len(content) > MAX_UPLOAD_BYTES:
        raise DatasetFileError("FILE_TOO_LARGE", {"max_mb": 50})

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception:
        raise DatasetFileError("FILE_UNREADABLE")


    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df.columns = [str(column).strip() for column in df.columns]

    if df.empty or df.shape[1] == 0:
        raise DatasetFileError("DATASET_NO_ROWS")

    if len(set(df.columns)) != len(df.columns):
        raise DatasetFileError("DATASET_DUPLICATE_COLUMNS", {"columns": sorted({c for c in df.columns if list(df.columns).count(c) > 1})})

    return df.reset_index(drop=True)


def read_uploaded_dataframe(upload):

    content = upload.file.read()
    filename = upload.filename or "dataset.xlsx"

    if _extension(filename) not in ALLOWED_EXTENSIONS:
        filename = filename + ".xlsx"

    return read_bytes(content, filename)


def read_dataset_file(path):

    with open(path, "rb") as handle:
        return read_bytes(handle.read(), path)
