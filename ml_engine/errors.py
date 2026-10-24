


ERROR_MESSAGES = {

    "VALIDATION_ERROR": "The request is incomplete or invalid.",
    "INTERNAL_ERROR": "Unexpected server error.",
    "AUTH_REQUIRED": "Please sign in to continue.",
    "AUTH_INVALID_SESSION": "Your session has expired. Please sign in again.",
    "AUTH_INVALID_CREDENTIALS": "Email or password is incorrect.",
    "AUTH_NAME_TOO_SHORT": "Name must be at least 2 characters.",
    "AUTH_INVALID_EMAIL": "The email address is not valid.",
    "AUTH_PASSWORD_TOO_SHORT": "Password must be at least 6 characters.",
    "AUTH_EMAIL_EXISTS": "An account with this email already exists.",


    "FILE_TYPE_NOT_SUPPORTED": "Only Excel (.xlsx) and CSV files are supported.",
    "FILE_EMPTY": "The file is empty.",
    "FILE_TOO_LARGE": "The file is larger than {max_mb} MB.",
    "FILE_UNREADABLE": "The file could not be read. Make sure it is a valid Excel or CSV file.",
    "DATASET_NO_ROWS": "The dataset contains no data rows.",
    "DATASET_DUPLICATE_COLUMNS": "Some column names are duplicated: {columns}.",
    "TOO_FEW_ROWS": "The dataset has only {rows} rows; at least {min_rows} are required.",
    "HTTP_ERROR": "The request could not be completed.",
    "DATASET_TOO_SMALL": "The dataset has only {rows} rows; at least {min_rows} are required.",
    "NO_USABLE_FEATURES": "No usable feature columns remain after validation.",
    "SCHEMA_MISMATCH": "The columns of the new file do not match this project (missing: {missing}; extra: {extra}).",



    "PROJECT_NOT_FOUND": "Project not found.",
    "PROJECT_NAME_EMPTY": "Project name cannot be empty.",
    "PROJECT_NOT_READY": "Finish the initial analysis of this project before adding new data.",
    "PROJECT_NO_DATA": "No data has been stored for this project.",
    "PROJECT_NOT_CONFIGURED": "The analysis settings of this project are not complete yet.",
    "VERSION_FIRST_NOT_DELETABLE": "The first version cannot be deleted; delete the whole project instead.",
    "VERSION_ONLY_LATEST_DELETABLE": "Only the latest version can be deleted.",
    "INVALID_PROBLEM_TYPE": "Unsupported analysis type.",
    "INVALID_TARGET_MODE": "Unsupported target mode.",
    "TARGET_NOT_FOUND": "The target column was not selected or does not exist.",
    "TARGET_TOO_FEW_CLASSES": "The target must contain at least two classes.",
    "TARGET_SINGLE_SAMPLE_CLASS": "Some classes of this target have fewer than two samples: {classes}.",
    "TARGET_TOO_MANY_CLASSES": "The target has {classes} classes for {rows} rows; there is not enough data per class.",
    "PSEUDO_TARGET_MISSING": "Generate the pseudo-target first.",
    "PSEUDO_TARGET_NO_NUMERIC": "A pseudo-target needs at least one numeric, non-identifier column.",
    "PSEUDO_TARGET_NO_VARIATION": "The selected features do not vary enough to build target classes.",
    "ALGORITHM_NOT_ALLOWED": "Algorithm '{algorithm}' is not eligible for these settings.",
    "ALGORITHM_UNKNOWN": "Algorithm '{algorithm}' is not defined for this analysis type.",
    "CLUSTER_COUNT_INVALID": "The number of clusters must be an integer between 2 and {max}.",
    "CLUSTERING_TOO_FEW_ROWS": "Clustering needs at least {min_rows} rows.",
    "SPLIT_NOT_POSSIBLE": "The data is too small to create independent training and test sets.",


    "LLM_NOT_CONFIGURED": "The LLM service is not configured (OPENROUTER_API_KEY is missing).",
    "LLM_AUTH_ERROR": "The LLM provider rejected the API key.",
    "LLM_RATE_LIMIT": "The LLM provider rate limit was reached.",
    "LLM_TIMEOUT": "The LLM did not answer within the time limit.",
    "LLM_CONNECTION_ERROR": "The LLM provider could not be reached.",
    "LLM_MODEL_UNAVAILABLE": "The requested LLM model is not available.",
    "LLM_INVALID_RESPONSE": "The LLM answer was not valid JSON or did not match the schema.",
    "LLM_INVALID_COLUMNS": "The LLM proposed columns that do not exist in the dataset.",
    "LLM_UNAVAILABLE": "All configured LLM models failed: {reasons}.",
}


class AppError(ValueError):



    status_code = 400

    def __init__(self, code, params=None, status=None, message=None):
        self.code = code
        self.params = {key: _plain(value) for key, value in (params or {}).items()}
        if status is not None:
            self.status_code = status
        self.message = message or _render(code, self.params)
        super().__init__(self.message)

    def to_dict(self):
        return {"code": self.code, "message": self.message, "params": self.params}


def _plain(value):
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return str(value)


def _render(code, params):
    template = ERROR_MESSAGES.get(code, code)
    printable = {
        key: ", ".join(value) if isinstance(value, list) else value
        for key, value in params.items()
    }
    try:
        return template.format(**printable)
    except (KeyError, IndexError, ValueError):
        return template
