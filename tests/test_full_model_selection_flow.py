from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.model_selection.context_builder import ModelSelectionContextBuilder
from ml_engine.model_selection.scoring_engine import ScoringEngine
from ml_engine.preprocessing.pipeline import PreprocessingPipeline

file = "data/customer_dataset.xlsx"
analysis_result = DatasetAnalyzer().analyze(file)
clean_dataframe = PreprocessingPipeline(analysis_result["dataframe"]).process()
context = ModelSelectionContextBuilder().build(analysis_result,clean_dataframe,user_preference)


recommendations = ScoringEngine().recommend(context)