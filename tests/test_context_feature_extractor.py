from ml_engine.model_selection.context_feature_extractor import (ContextFeatureExtractor)
from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)
from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.preprocessing.pipeline import PreprocessingPipeline

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

    "classification"

)

extractor = ContextFeatureExtractor()
features = extractor.extract(context)
print(features)