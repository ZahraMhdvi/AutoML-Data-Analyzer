
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.model_selection.application.model_selection_application import ModelSelectionApplication

app = ModelSelectionApplication()
preferences = {
    "main_goal": "accuracy",
    "data_growth": "static_data",
    "feature_dimension": "normal_dimension",
    "noise_presence": "has_noise"

}

response = app.run(
    "data/customer_dataset.xlsx",
    "classification",
    "Churn",
    preferences,
    CLASSIFICATION_ALGORITHMS

)

print(response)