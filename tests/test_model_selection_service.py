from ml_engine.model_selection.application.model_selection_service import ModelSelectionService
from ml_engine.model_selection.user_answer_handler import (UserAnswerHandler)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)

FILE_PATH = "data/customer_dataset.xlsx"
analysis_result = DatasetAnalyzer().analyze(FILE_PATH)
pipeline = PreprocessingPipeline(
    analysis_result["dataframe"],
    "classification",
    "Churn"
)
processed = pipeline.process()
context = (
    ModelSelectionContextBuilder()
    .build(
        analysis_result,
        processed["dataframe"],
        {},
        "classification"

    )
)

answers = {
    "main_goal": "accuracy",
    "data_growth": "static_data",
    "feature_dimension": "normal_dimension",
    "noise_presence": "has_noise"
}
preferences = (UserAnswerHandler().create_preferences(answers,"classification"))

service = ModelSelectionService()
results = service.select(

    context,
    preferences,
    CLASSIFICATION_ALGORITHMS

)

for result in results:
    print(result)