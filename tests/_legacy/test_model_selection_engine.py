from ml_engine.model_selection.model_selection_engine import (ModelSelectionEngine)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.preprocessing.pipeline import (PreprocessingPipeline)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)

FILE_PATH = "data/customer_dataset.xlsx"
analysis_result = DatasetAnalyzer().analyze(FILE_PATH)
pipeline = PreprocessingPipeline(
    analysis_result["dataframe"],
    "classification",
    "Churn"
)
processed = pipeline.process()
context = ModelSelectionContextBuilder().build(
    analysis_result,
    processed["dataframe"],
    {},
    "classification")

engine = ModelSelectionEngine()
preferences = {
    "high_accuracy": True,
    "handles_noise": True
}


results = engine.select_models(

    context,

    preferences,

    CLASSIFICATION_ALGORITHMS)

for result in results:

    print(result)